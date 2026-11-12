"""Match a fresh current111 non-opening development overrun and its physical/virtual budget."""
import os
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from profile_live109_target import HEADER,main,prepare
from profile_live111_first import exact_build


def instrument(src,enabled,case):
    prepare(src,enabled,case,reference_name="live111")
    header=HEADER.replace("inline unsigned count = 0;",'''inline unsigned count = 0;
inline bool active=false;
inline void begin(int type,int round){active=type==CODEX_TARGET_TYPE&&round==CODEX_TARGET_ROUND;}''')
    header=header.replace("if (type != CODEX_TARGET_TYPE || round != CODEX_TARGET_ROUND || count >= 96)","if (!active || count >= 96)")
    (src/"codex_trace.h").write_text(f"#define CODEX_TARGET_TYPE {case['type']}\n#define CODEX_TARGET_ROUND {case['round']}\n"+header,encoding="utf8",newline="\n")
    path=src/"main.cpp";text=path.read_text(encoding="utf8")
    anchor="                bot.play_turn();";assert text.count(anchor)==2
    text=text.replace(anchor,'''#if CODEX_FINE
                codex_trace::begin(static_cast<int>(bc::self().champion_name()),bc::round_number());
                CODEX_FINE_MARK("main_begin",0,0);
#endif
                bot.play_turn();''')
    path.write_text(text,encoding="utf8",newline="\n")
    path=src/"bot.cpp";text=path.read_text(encoding="utf8")
    text=re.sub(r'CODEX_FINE_MARK\("([a-zA-Z0-9_]+)", static_cast<int>\(type\), round\);',r'CODEX_FINE_MARK("\1",static_cast<int>(type),round,nn_spent,field_calls);',text)
    path.write_text(text,encoding="utf8",newline="\n")


if __name__ == "__main__":
    rows=read(HERE/"LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    choices=[(r,e) for r in rows if r["side"]=="A" for e in r["early_events"] if e["round"]>1]
    row,event=min(choices,key=lambda p:(p[0]["map_hash"],p[1]["round"],p[1]["actor"],p[0]["opponent"]))
    directory=bench.CACHE/"live111-late-turn-baseline";directory.mkdir()
    old=bench.CACHE/"live111-large-development"/row["opponent"]/f"{row['map']}-A-stock111"
    (archive,)=old.glob("*.repl26a");replay=directory/"raw.repl26a"
    with ZipFile(archive) as z:
        with replay.open("xb") as f:f.write(z.read("replay.repl26a"))
    turn=directory/"turn.json"
    subprocess.run(["node",HERE/"trace_turn.mjs",replay,str(event["round"]),"0",str(event["actor"]),turn],cwd=bench.ROOT,env={**os.environ,"NFS_REPLAY_ENGINE":"3.0.0"},check=True)
    view=read(turn)
    case={"stage":"late111","round":event["round"],"actor":event["actor"],"type":view["observation"]["actor"]["type"],"champion":event["name"],**{k:row[k] for k in ("map","side","opponent","map_hash")},
          "traces":{"base":{"path":turn.relative_to(bench.ROOT).as_posix(),"sha256":bench.digest(turn)}}}
    write(HERE/"LIVE111_LATE_TURN_PLAN.json",{"selection":"First stable-mapSHA sideA baseline event afterR1,then round/actor/opponent;independent dev only","case":case})
    main(label="late111",cases=[case],prepare_fn=instrument,build_fn=exact_build,expected_hash=read(HERE/"LIVE111_SOURCE_VERIFIED.json")["wasm_sha256"],project_prefix="live111-target")
