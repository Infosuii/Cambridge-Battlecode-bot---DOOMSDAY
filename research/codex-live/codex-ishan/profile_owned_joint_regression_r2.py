"""EXP253 repair: rerun the unchanged frozen EXP252 development case."""
from engine3_pool import HERE,read
from profile_owned_joint_regression import instrument
from profile_live109_target import main
from profile_live111_first import exact_build

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')
    main(label='ownedjointregression111r2',cases=[plan['case']],prepare_fn=instrument,
         build_fn=exact_build,expected_hash=plan['source_build'],project_prefix='live111-owned-joint-target')
