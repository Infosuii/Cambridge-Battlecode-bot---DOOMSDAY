"""Fit a bounded tactical-intent tree; evaluate on entire excluded opponent teams before export."""
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
from numpy_tree import DecisionTreeClassifier,GroupKFold,accuracy_score,balanced_accuracy_score,confusion_matrix
from policy_features import features,label,NAMES

root=Path(__file__).resolve().parents[2]
rows=json.loads((root/'research/v75/duel_v74.json').read_text())
X=[];Y=[];G=[]
for r in rows:
    us=0 if r['side']=='a' else 1
    d=json.loads((root/'artifacts/local-only/duel-v74'/r['matchId']/'policy500.json').read_text())
    for t in d['turns']:
        if t['team']==us or t['nd']>6 or not t['foes'] or t['round']<2:continue
        X.append(features(t));Y.append(label(t));G.append(r['opponent'])
X=np.asarray(X,dtype=np.float32);Y=np.asarray(Y);G=np.asarray(G)
report=dict(rows=len(Y),classes=dict(Counter(map(int,Y))),features=NAMES,folds=[])
for train,test in GroupKFold(4).split(X,Y,G):
    model=DecisionTreeClassifier(max_depth=5,min_samples_leaf=250,random_state=1)
    model.fit(X[train],Y[train]);pred=model.predict(X[test]);prob=model.predict_proba(X[test]).max(axis=1)
    use=prob>=0.65
    report['folds'].append(dict(excluded_teams=sorted(set(G[test])),n=len(test),accuracy=accuracy_score(Y[test],pred),
        balanced_accuracy=balanced_accuracy_score(Y[test],pred),majority_accuracy=float(np.bincount(Y[test]).max()/len(test)),
        confident_coverage=float(use.mean()),confident_accuracy=accuracy_score(Y[test][use],pred[use]) if use.any() else None,
        confusion=confusion_matrix(Y[test],pred,labels=[0,1,2]).tolist()))
model=DecisionTreeClassifier(max_depth=5,min_samples_leaf=250,random_state=1).fit(X,Y)
tree=model.tree_;values=tree.value[:,0,:];values=values/values.sum(axis=1,keepdims=True)
pred=model.classes_[values.argmax(axis=1)].astype(int);conf=values.max(axis=1)
fmt=lambda a:','.join(str(int(x)) for x in a)
floats=lambda a:','.join(f'{float(x):.8g}f' if float(x)%1 else f'{float(x):.1f}f' for x in a)
header='''// Actual-observation top-team tactical intent, GroupKFold by whole opponent team. Classification is not causal value.
#pragma once
namespace intent83 {
'''
for name,arr in [('feature',tree.feature),('left',tree.children_left),('right',tree.children_right),('prediction',pred)]:
    header+=f'inline constexpr int {name}[]={{'+fmt(arr)+'};\n'
for name,arr in [('threshold',tree.threshold),('confidence',conf)]:
    header+=f'inline constexpr float {name}[]={{'+floats(arr)+'};\n'
header+='inline int predict(const float* f,float& p){int n=0;while(feature[n]>=0)n=f[feature[n]]<=threshold[n]?left[n]:right[n];p=confidence[n];return prediction[n];}\n}\n'
(root/'research/v81/intent_model.h').write_text(header)
report['nodes']=tree.node_count
report['method']='NumPy histogram CART, 16 training-only quantile bins, depth 5, min leaf 250'
report['depth']=5;report['minimum_leaf']=250;report['confidence_backoff']=0.65
np.savez_compressed(root/'artifacts/tmp/v67/intent83_parity.npz',features=X[::50],prediction=model.predict(X[::50]),confidence=model.predict_proba(X[::50]).max(axis=1))
(root/'research/v81/intent_validation.json').write_text(json.dumps(report,indent=1)+'\n')
print(json.dumps(report,indent=1))
