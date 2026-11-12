# Agent2 pretrained native baseline, reproduced locally

Source commit afb43b886fc348006d48d4f4feb830c16cba5533; checkpoint research/agent2-neural/models/student_i2m.pt, blob9db47c99cebb92f83475e39954dd86294a9f69f0, SHA25605052b6e8ddeb8eaa4cef760b8b24dda9cfee794207b0a2d12d7b06bfae9e5ec.28889 trainable parameters plus216 preprocessing buffers; native layout2/500 fields.

This uses the checkpoint in its matching native encoder/runtime, not CL1. Copy the pinned rl_workspace/v4/bots/v92/src base to a new bot; use code/{nn_model.py,nn_export.py,nn_mkbot.py,nnrec.cpp,nn_infer.h} from the source commit. Keep torch.load(weights_only=True,map_location=cpu). Export with NN_LAYOUT=2 and NN_STUDENT=16x64. The native scripts expect workspace agent2/lab and v4; this Mac uses an isolated native_workspace with v4 linked to the local project and cambc.exe linked to the official Mac CLI. No platform command is invoked.

Factory flags tested: A2_NN=11 A2_NN_MACRO=1 A2_NN_FAST=1 A2_NN_VALID=1 A2_NN_BEH=0 A2_NN_ENS=2 A2_NN_LIVE=1 A2_NN_LAZY=1 A2_NN_NNUE=1 A2_NN_Q16=1 A2_NN_SGAUTO=1 A2_FIELD_MARGIN=3000 A2_NN_FIELDS_FIRST=1. Local output bot jd-a2-seed-e3, built in release with cambc4.0.0/wasi-sdk33.

Six deterministic real-fuel games:4wins,0crashes,110fuel-outs for this bot. This is Agent2's baseline reproduced here, not an RL improvement by JOHNDOE. Stronger than the compact testbed in this small check, but not a reliable overall win-rate estimate or a platform promotion approval. Do not send these fuel-failed games to the strict CL1 PPO consumer. Native-policy fine-tuning needs a compatible collector that records actual effective/stale inputs and executed-action probabilities through the blend/fallback; it cannot silently reuse CL1 rows or proposed-action probabilities.
