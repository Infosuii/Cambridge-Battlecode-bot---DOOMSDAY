"""Cooperative terminal-win objective with bounded potential-based shaping.

Undiscounted episodic return telescopes to outcome minus the initial potential.
Only previous-round native score samples enter a decision's potential: native
timelines include events later in the named round. The value bootstrap is zero
at termination, including a last neural decision long before the match ends.
"""
import numpy as np


def potential(lead, round_number):
    index=min(max(int(round_number)-1,0),len(lead)-1)
    return .1*np.tanh(float(lead[index])/1000.)


def gae_game(rows, lead, outcome, values, gamma=1., lam=.995):
    if gamma!=1.:raise ValueError('This win-objective profile requires undiscounted episodic return')
    if outcome not in (-1.,0.,1.) or not len(lead) or len(rows)!=len(values):
        raise ValueError('Invalid episode inputs')
    adv=np.zeros(len(rows),dtype=np.float32);ret=np.zeros_like(adv);by_body={}
    for i,row in enumerate(rows):by_body.setdefault(row['me'],[]).append(i)
    for indices in by_body.values():
        acc=0.
        for pos in range(len(indices)-1,-1,-1):
            i=indices[pos];rnd=rows[i]['r'];phi=potential(lead,rnd)
            if pos==len(indices)-1:
                # Absorbing terminal potential and value both equal zero.
                delta=float(outcome)-phi-float(values[i]);acc=delta
            else:
                j=indices[pos+1];dt=rows[j]['r']-rnd
                if dt<=0:raise ValueError('Non-increasing decisions for one body')
                reward=potential(lead,rows[j]['r'])-phi
                delta=reward+float(values[j])-float(values[i])
                acc=delta+lam**dt*acc
            adv[i]=acc;ret[i]=acc+float(values[i])
    if not np.isfinite(adv).all() or not np.isfinite(ret).all():raise ValueError('Non-finite team-win returns')
    return adv,ret
