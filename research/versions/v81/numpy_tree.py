"""Small histogram CART classifier, NumPy only. Bins are fitted on training data, never validation rows."""
from types import SimpleNamespace
import numpy as np

class DecisionTreeClassifier:
    def __init__(self,max_depth=5,min_samples_leaf=250,random_state=1):
        self.depth=max_depth;self.minimum=min_samples_leaf;self.classes_=np.arange(3)
    def fit(self,X,y):
        cuts=[np.unique(np.quantile(X[:,j],np.linspace(0,1,17)[1:-1])) for j in range(X.shape[1])]
        bins=np.stack([np.searchsorted(c,X[:,j],side='left') for j,c in enumerate(cuts)],axis=1)
        feature=[];threshold=[];left=[];right=[];value=[]
        def build(ids,depth):
            n=len(feature);feature.append(-2);threshold.append(-2.);left.append(-1);right.append(-1)
            count=np.bincount(y[ids],minlength=3).astype(float);value.append(count)
            if depth==self.depth or len(ids)<2*self.minimum:return n
            parent=len(ids)-(count@count)/len(ids);best_gain=1e-8;best=None
            for j,c in enumerate(cuts):
                if len(c)==0:continue
                h=np.bincount(bins[ids,j]*3+y[ids],minlength=(len(c)+1)*3).reshape(-1,3)
                l=np.cumsum(h,axis=0)[:-1];r=count-l;ln=l.sum(axis=1);rn=r.sum(axis=1)
                valid=(ln>=self.minimum)&(rn>=self.minimum)
                gain=parent-(ln-(l*l).sum(axis=1)/np.maximum(ln,1))-(rn-(r*r).sum(axis=1)/np.maximum(rn,1))
                gain[~valid]=-1;k=int(gain.argmax())
                if gain[k]>best_gain:best_gain=float(gain[k]);best=(j,k,float(c[k]))
            if best is None:return n
            j,k,t=best;mask=bins[ids,j]<=k
            feature[n]=j;threshold[n]=t;left[n]=build(ids[mask],depth+1);right[n]=build(ids[~mask],depth+1)
            return n
        build(np.arange(len(y)),0)
        self.tree_=SimpleNamespace(feature=np.array(feature),threshold=np.array(threshold),children_left=np.array(left),
            children_right=np.array(right),value=np.asarray(value)[:,None,:],node_count=len(feature))
        return self
    def predict_proba(self,X):
        nodes=np.zeros(len(X),dtype=int);t=self.tree_
        for _ in range(self.depth):
            active=t.feature[nodes]>=0
            ids=np.flatnonzero(active)
            if not len(ids):break
            nn=nodes[ids];nodes[ids]=np.where(X[ids,t.feature[nn]]<=t.threshold[nn],t.children_left[nn],t.children_right[nn])
        v=t.value[nodes,0,:];return v/v.sum(axis=1,keepdims=True)
    def predict(self,X):return self.predict_proba(X).argmax(axis=1)

class GroupKFold:
    def __init__(self,n):self.n=n
    def split(self,X,y,G):
        names=sorted(set(G))
        for k in range(self.n):
            test=np.isin(G,names[k::self.n]);yield np.flatnonzero(~test),np.flatnonzero(test)

def accuracy_score(a,b):return float(np.mean(a==b))
def balanced_accuracy_score(a,b):return float(np.mean([np.mean(b[a==k]==k) for k in np.unique(a)]))
def confusion_matrix(a,b,labels):
    return np.bincount(a*len(labels)+b,minlength=len(labels)**2).reshape(len(labels),len(labels))
