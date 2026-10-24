"""Create a labelled synthetic UNTRAINED direct-policy artifact. No games, fitting, registration or installation."""
import argparse
from pathlib import Path
from nfs.policy.model import build_model,init_untrained
from nfs.policy.export import export_model

ROOT=Path(__file__).resolve().parents[2]

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--name",default="policy_v2_untrained")
    ap.add_argument("--seed",type=int,default=20261024)
    ap.add_argument("--zero-logits",action="store_true")
    args=ap.parse_args()
    out=args.out.resolve()
    if not out.is_relative_to(ROOT) or "references" in out.relative_to(ROOT).parts:
        raise SystemExit("output must stay inside workspace, outside references")
    model=init_untrained(build_model("policy_v2"),args.seed,zero_logits=args.zero_logits)
    man=export_model(model,args.name,out,"untrained",dict(synthetic=True,source="seeded synthetic initialization",
                     seed=args.seed,zero_logits=args.zero_logits,training_games=0,parameter_updates=0))
    print(f'{man["name"]}: {man["n_params"]} f32 params, {man["checksum"]}, interpretation2/kernel1, UNTRAINED')
