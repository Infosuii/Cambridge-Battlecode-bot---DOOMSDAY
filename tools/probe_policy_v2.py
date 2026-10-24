"""Prepare a scratch-only official policy-v2 component fuel probe.

Default action prepares sources only. --run explicitly builds and runs the frozen reused calibration maps.
Real capture/SDK builders are measured after teacher decisions; dense kernels and log fixtures are synthetic.
No action executor, optimizer, training collector, activation or submission is invoked by this probe.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROBE = r'''
// Diagnostic component probe only. Teacher decisions are already complete when run() is called.
#include "bot.h"
#include "nn_policy_options.h"
#include "nn_policy_state.h"
#include "nn_policy_observation.h"
#include "nn_policy_model.h"
#include "nn_policy_installed.h"
#include "nn_policy_log.h"
#include <cstdio>
#include <algorithm>
namespace d=cambc::detail;

namespace {
constexpr int kStages=21;
constexpr std::uint64_t kReserve=8000,kMinimum=65000;
constinit int g_stage=0,g_repetition=0,g_last=-1,g_pending=-1;
constinit volatile float g_sink=0;
constinit float g_observation[nnpobs::kObsDim]{},g_context[nnm::kMaxCtx]{},g_features[16*12]{},g_logits[16]{};
constinit std::uint32_t g_ids[16]{};
constinit std::uint8_t g_legal[16]{};
constinit nnm::Scratch g_scratch{};
constinit nnpobs::Raw g_raw{};
constinit nnpc::Decision g_decision{};
constinit nnp::OptionsState g_state{};
using Build=bool(*)(const Bot&,const nnp::OptionsState&,nnpc::Decision&);
const char* label(int stage) {
    constexpr const char* names[kStages]={"capture_real","strategy_builder_real","objective_builder_real","role_builder_real",
        "bank_builder_real","shop_builder_real","move_builder_real","combat_builder_real","engage_builder_real",
        "encoder_synthetic_dense","head1_synthetic_K16","head2_synthetic_K16","head3_synthetic_K16",
        "head4_synthetic_K16","head5_synthetic_K16","head6_synthetic_K16","head7_synthetic_K16","head8_synthetic_K16",
        "context_enqueue_mixed","decision_enqueue_synthetic_K16","execution_enqueue_synthetic"};
    if(stage>=0&&stage<kStages)return names[stage];
    return g_pending==18?"record_flush_context_mixed":g_pending==19?"record_flush_decision_synthetic_K16":"record_flush_execution_synthetic";
}
nnp_log::Header header(bool decision) {
    nnp_log::Header h{};h.obs_hash=nnpobs::kObsSchemaHash;h.action_hash=nnpc::kActionSchemaHash;
    h.round=static_cast<int>(bc::round_number());
    // Reserved synthetic fixture identity: these records are never eligible for training.
    h.champion=0xffffffffu;h.snapshot=1;h.decision_id=decision?1:0;return h;
}
void fixture() {
    for(int i=0;i<nnpobs::kObsDim;++i)g_observation[i]=0.1f+float(i%7)*0.1f;
    for(int i=0;i<nnpobs::kAllyRows;++i)g_observation[90+i]=1;
    for(int i=0;i<nnpobs::kEnemyRows;++i)g_observation[167+i]=1;
    for(int i=0;i<nnm::kMaxCtx;++i)g_context[i]=0.125f;
    for(int i=0;i<16*12;++i)g_features[i]=0.2f+float(i%5)*0.1f;
    for(int i=0;i<16;++i)g_ids[i]=static_cast<std::uint32_t>(i),g_legal[i]=1,g_logits[i]=0;
}
}

struct nn_policy_probe_access {
    // Banking after a completed teacher action is only save, even with gems. Measure the live
    // path on a dedicated next turn, then end that probe turn instead of restarting the teacher.
    static bool before(Bot& b) {
        if(g_stage!=4||g_pending>=0||g_repetition>=3||!b.inited)return false;
        d::champion_info me{};std::uint32_t gems=0;
        if(d::sdk_champion(b.my_id,&me)!=0||d::sdk_champion_gems(b.my_id,&gems)!=0||!gems||
           !(me.state&1u)||(me.state&((1u<<1)|(1u<<2)|(1u<<5)|(1u<<6)|(1u<<7)|(1u<<12))))return false;
        b.round=static_cast<int>(bc::round_number());b.refresh_self();b.w.update(b.round);state(b);
        const auto required=nnp::bank_candidate_fuel(b);
        if(required>bc::fuel_remaining()||bc::fuel_remaining()-required<16000)return true;
        const auto first=bc::round_number();const auto start=bc::fuel_remaining();
        const bool ok=nnp::build_bank(b,g_state,g_decision);
        const auto after=bc::fuel_remaining();const auto last=bc::round_number();
        const bool overrun=first!=last||after>start;const auto cost=overrun?0:start-after;
        const char* status=overrun?"overrun":cost>required?"bound_exceeded":ok?"ok":"refused";
        std::printf("NFP2 component=bank_builder_real stage=4 repetition=%d status=%s fuel=%llu required=%llu available=%llu K=%d synthetic=0 before_fuel=%llu after_fuel=%llu before_round=%u after_round=%u\n",
            g_repetition,status,static_cast<unsigned long long>(cost),static_cast<unsigned long long>(required),
            static_cast<unsigned long long>(start),g_decision.K,static_cast<unsigned long long>(start),static_cast<unsigned long long>(after),first,last);
        g_last=static_cast<int>(last);
        if(ok&&g_decision.K>1)++g_stage;
        return true;
    }
    static std::uint64_t bound(const Bot& b,int stage) {
        if(stage>=1&&stage<=3) {
            constexpr nncfg::H heads[]={nncfg::H::strategy,nncfg::H::objective,nncfg::H::role};
            return nnp::strategy_candidate_fuel(b,heads[stage-1]);
        }
        if(stage==4)return nnp::bank_candidate_fuel(b);
        if(stage>=6&&stage<=8) {
            constexpr nncfg::H heads[]={nncfg::H::move,nncfg::H::combat,nncfg::H::engage};
            return nnp::tactics_candidate_bound(b,g_state,heads[stage-6]);
        }
        return 40000;
    }
    static void state(const Bot& b) {
        g_state={};g_state.goal=b.pos;
        const auto observed=nnp::observation_goal();
        if(observed.x>=0&&observed.y>=0&&observed.x<b.w.width&&observed.y<b.w.height)g_state.goal=observed;
        // Public static group order; never borrow the teacher's ranked target_group or mode.
        for(std::size_t gi=0;gi<b.w.groups.size();++gi) {
            if(!b.w.has_field(static_cast<int>(gi))||b.w.groups[gi].camps.empty()||b.w.group_distance(static_cast<int>(gi),b.pos)==kUnreach)continue;
            const int ci=b.w.groups[gi].camps.front();
            if(ci>=0&&ci<static_cast<int>(b.w.camps.size())) {
                g_state.objective=static_cast<int>(gi);g_state.goal=b.w.camps[ci].pos;break;
            }
        }
    }
    static void run(Bot& b) {
        const int round=static_cast<int>(bc::round_number());
        if(!b.inited||b.was_dead||b.hp<=0||round==g_last||(g_repetition>=3&&g_pending<0))return;
        g_last=round;
        const auto available=bc::fuel_remaining();if(available<kMinimum)return;
        state(b);
        const int stage=g_pending>=0?-1:g_stage;
        if(stage==4)return; // dedicated live banking probe owns this stage
        const auto required=stage<0?std::uint64_t(nnp_log::next_line_bytes())*32+14000:bound(b,stage);
        if(required>available||available-required<kReserve) {
            std::printf("NFP2 component=%s stage=%d repetition=%d status=missing_bound fuel=0 required=%llu available=%llu K=0 synthetic=%d\n",
                label(stage),stage,g_repetition,static_cast<unsigned long long>(required),static_cast<unsigned long long>(available),stage>=9||stage<0);
            if(stage>=0){if(++g_stage==kStages)g_stage=0,++g_repetition;}
            return;
        }
        fixture();
        // Preserve a real compact capture for context cost without charging it to the enqueue kernel.
        bool prepared=true;
        if(stage==18)prepared=nnpobs::capture(b,g_observation);
        if(stage==19)nnpm::direct_logits(nnp::kInstalled,6,0,g_context,g_features,16,g_legal,g_logits);
        if(bc::fuel_remaining()<required+kReserve) {
            std::printf("NFP2 component=%s stage=%d repetition=%d status=missing_preparation fuel=0 required=%llu available=%llu K=0 synthetic=%d\n",
                label(stage),stage,g_repetition,static_cast<unsigned long long>(required),static_cast<unsigned long long>(bc::fuel_remaining()),stage>=9||stage<0);
            if(stage>=0){if(++g_stage==kStages)g_stage=0,++g_repetition;}
            return;
        }
        const auto before_round=bc::round_number();
        const auto before=bc::fuel_remaining();bool ok=prepared;int K=stage<0&&g_pending==19?16:0;
        try {
            if(stage<0)ok=nnp_log::flush_one();
            else if(stage==0)ok=nnpobs::capture(b,g_observation),g_sink=g_observation[0];
            else if(stage>=1&&stage<=8) {
                constexpr Build builders[8]={nnp::build_strategy,nnp::build_objective,nnp::build_role,nnp::build_bank,
                    nnp::build_shop,nnp::build_move,nnp::build_combat,nnp::build_engage};
                ok=builders[stage-1](b,g_state,g_decision);K=g_decision.K;
                if(K)g_sink=g_decision.feat[0];
            } else if(stage==9)nnpm::encode(*nnp::kInstalled.kernel,g_observation,g_context,g_scratch),g_sink=g_context[0];
            else if(stage>=10&&stage<=17) {
                K=16;nnpm::direct_logits(nnp::kInstalled,stage-9,0,g_context,g_features,16,g_legal,g_logits);g_sink=g_logits[15];
            } else if(stage==18) {
                nnp_log::ContextRec record{};record.h=header(false);record.raw=g_observation;record.bytes=sizeof g_observation;
                ok=prepared&&nnp_log::enqueue_context(record);
            } else if(stage==19) {
                K=16;nnp_log::DecisionRec record{};record.h=header(true);record.head=6;record.K=16;record.chosen=0;
                record.selected_id=g_ids[0];record.id=g_ids;record.legal=g_legal;record.feat=g_features;record.logits=g_logits;
                ok=nnp_log::enqueue_decision(record);
            } else if(stage==20) {
                nnp_log::ExecutionRec record{};record.h=header(true);record.executed_id=0;record.outcome=nnp_log::kExecuted;
                ok=nnp_log::enqueue_execution(record);
            }
        } catch(...) {ok=false;}
        const auto after=bc::fuel_remaining();
        const auto after_round=bc::round_number();
        const bool overrun=before_round!=after_round||after>before;
        const auto cost=overrun?0:before-after;
        const char* status=overrun?"overrun":cost>required?"bound_exceeded":ok?"ok":"refused";
        std::printf("NFP2 component=%s stage=%d repetition=%d status=%s fuel=%llu required=%llu available=%llu K=%d synthetic=%d before_fuel=%llu after_fuel=%llu before_round=%u after_round=%u\n",
            label(stage),stage,g_repetition,status,static_cast<unsigned long long>(cost),
            static_cast<unsigned long long>(required),static_cast<unsigned long long>(before),K,stage>=9||stage<0,
            static_cast<unsigned long long>(before),static_cast<unsigned long long>(after),before_round,after_round);
        if(stage<0)g_pending=-1;
        else {
            if(stage>=18&&!nnp_log::queue_empty())g_pending=stage;
            if(++g_stage==kStages)g_stage=0,++g_repetition;
        }
    }
};
namespace nnpolicyprobe { bool before(Bot& b){return nn_policy_probe_access::before(b);} void run(Bot& b){nn_policy_probe_access::run(b);} }
'''


def prepare(destination: Path) -> Path:
    destination = destination.resolve()
    scratch = (ROOT / "artifacts/tmp").resolve()
    if not destination.is_relative_to(scratch) or destination == scratch:
        raise ValueError("a fresh dedicated artifacts/tmp destination is required")
    if destination.exists():
        raise FileExistsError(destination)
    sys.path.insert(0, str(ROOT / "tools"))
    from install_policy_v2 import install
    bot = install(destination / "bot", "direct_untrained")
    source = bot / "src"
    path = source / "bot.cpp"
    text = path.read_text(encoding="utf-8")
    text = "class Bot; namespace nnpolicyprobe { bool before(Bot&); }\n"+text
    hook = "if(nnp::play_turn(*this))return;"
    if text.count(hook) != 1:
        raise ValueError("the direct dispatch hook changed; refuse to prepare an ambiguous teacher probe")
    path.write_text(text.replace(hook, "if(nnpolicyprobe::before(*this))return; // live banking probe only"), encoding="utf-8")
    path = source / "bot.h"
    text = path.read_text(encoding="utf-8")
    friend = "friend struct nn_policy_tactics_access;"
    if text.count(friend) != 1:
        raise ValueError("cannot establish scratch probe read access")
    path.write_text(text.replace(friend, friend + "\n    friend struct nn_policy_probe_access;"), encoding="utf-8")
    path = source / "main.cpp"
    text = path.read_text(encoding="utf-8")
    if "int main() {" not in text or "bot.play_turn();" not in text:
        raise ValueError("main entry markers changed")
    text = text.replace("int main() {", "namespace nnpolicyprobe { void run(Bot&); }\nint main() {")
    text = text.replace("bot.play_turn();", "bot.play_turn(); nnpolicyprobe::run(bot);")
    # Probe queue is isolated: ordinary idle must not flush records outside the measured interval.
    text = text.replace("nnp::idle();", "(void)0; // probe owns bounded leftover output")
    path.write_text(text, encoding="utf-8")
    (source / "nn_policy_probe.cpp").write_text(PROBE, encoding="utf-8")
    metadata = dict(kind="component_probe", training_eligible=False, training_games=0, parameter_updates=0,
                    decisions="original teacher except dedicated live bank probe turns, which end after measuring", inputs="real permitted cached world after teacher actions",
                    capture_and_builders="real", dense_encoder_heads_and_log_fixtures="synthetic",
                    synthetic_record_champion=0xFFFFFFFF, release=True, fuel="official default",
                    cold_field_guard="strict tile-count/chunk bound; missing is never a passing measurement",
                    state="prepared only; no build or engine game has run")
    (destination / "probe.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return bot


PATTERN = re.compile(r"NFP2 component=(\S+) stage=(-?\d+) repetition=(\d+) status=(\S+) fuel=(\d+) required=(\d+) available=(\d+) K=(\d+) synthetic=(\d+)(?: before_fuel=(\d+) after_fuel=(\d+) before_round=(\d+) after_round=(\d+))?")


def parse_measurements(stdout: str, map_name: str) -> list[dict]:
    rows = []
    for match in PATTERN.finditer(stdout):
        component, stage, repetition, status, fuel, required, available, K, synthetic, before, after, first, last = match.groups()
        row = dict(map=map_name, component=component, stage=int(stage), repetition=int(repetition), status=status,
                   fuel=int(fuel), required=int(required), available=int(available), K=int(K), synthetic=bool(int(synthetic)))
        if before is not None:
            row.update(before_fuel=int(before), after_fuel=int(after), before_round=int(first), after_round=int(last))
        # Also reject legacy probe underflows instead of preserving a giant unsigned count as a valid cost.
        invalid = row["fuel"] > row["available"] or (before is not None and (int(after) > int(before) or first != last))
        if invalid:
            row.update(original_status=status, original_fuel=int(fuel), status="overrun", fuel=0, valid=False)
        elif status == "overrun":
            row["valid"] = False
        elif status == "bound_exceeded" or row["fuel"] > row["required"]:
            row.update(original_status=status, status="bound_exceeded", valid=False)
        else:
            row["valid"] = status == "ok"
        rows.append(row)
    return rows


def run(destination: Path, bot: Path, maps: list[str]) -> dict:
    sys.path.insert(0, str(ROOT / "python"))
    from nfs import engine
    from nfs.evaluate import protocol
    if maps != ["00rows", "01islands"]:
        raise ValueError("only the frozen reused policy-v2 component calibration maps are supported")
    wasm = engine.official_build(bot, destination / "probe.wasm")
    rows, games = [], []
    for name in maps:
        folder = destination / "matches" / name
        result = engine.run_match(wasm, ROOT / "references/builds/original.wasm", engine.MAPS / (name + ".map26a"), folder)
        games.append(result.row())
        rows.extend(parse_measurements(engine.team_stdout(folder, "A"), name))
    expected = {"capture_real", "strategy_builder_real", "objective_builder_real", "role_builder_real", "bank_builder_real",
                "shop_builder_real", "move_builder_real", "combat_builder_real", "engage_builder_real", "encoder_synthetic_dense",
                *(f"head{h}_synthetic_K16" for h in range(1, 9)), "context_enqueue_mixed", "decision_enqueue_synthetic_K16",
                "execution_enqueue_synthetic", "record_flush_context_mixed", "record_flush_decision_synthetic_K16",
                "record_flush_execution_synthetic"}
    passing = {row["component"] for row in rows if row["status"] == "ok" and (row['component']!='bank_builder_real' or row['K']>1)}
    violations = [row for row in rows if row["status"] in ("overrun", "bound_exceeded")]
    report = dict(kind="component_probe", training_eligible=False, release=True, fuel="official default",
                  map_label="reused_benchmark", source_sha256=engine.tree_sha256(bot / "src"), candidate_sha256=engine.sha256(wasm),
                  protocol_sha256=protocol.protocol_sha256(), games=games, measurements=rows,
                  missing_components=sorted(expected - passing), invalid_measurements=violations,
                  complete_components=expected <= passing and not violations,
                  warning="synthetic kernel/log fixtures; builder timing uses permitted real world; banking uses dedicated live probe turns; not strength evidence")
    (destination / "measurements.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/tmp/policy_v2_component_probe"))
    parser.add_argument("--run", action="store_true", help="explicitly build/run official release/default-fuel calibration games")
    parser.add_argument("--prepare-only", action="store_true", help="compatibility alias for the default preparation action")
    args = parser.parse_args()
    if args.run and args.prepare_only:
        parser.error("--run and --prepare-only are mutually exclusive")
    destination = (ROOT / args.out).resolve()
    bot = prepare(destination)
    if not args.run:
        print(f"Prepared only; no build/game executed: {bot}")
        return
    report = run(destination, bot, ["00rows", "01islands"])
    print(json.dumps({"complete_components": report["complete_components"], "missing_components": report["missing_components"]}, indent=2))
    if not report["complete_components"]:
        raise SystemExit("Component calibration incomplete; see explicit missing components in measurements.json")


if __name__ == "__main__":
    main()
