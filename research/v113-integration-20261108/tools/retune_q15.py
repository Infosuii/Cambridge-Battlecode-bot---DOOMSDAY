import os
os.environ['RETUNE_TRAINING']='q15-model-selection'
from blend_models import main as select_model
from retune_campaign import main
if __name__=='__main__':
    select_model()
    main()
