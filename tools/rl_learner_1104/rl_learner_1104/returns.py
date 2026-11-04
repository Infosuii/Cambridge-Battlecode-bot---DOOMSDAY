"""Duration-aware GAE. Death/respawn must NOT be supplied as termination.

Rewards are already discounted to the start of their decision interval.
next_values must come from the actual next observation, including final observations
at truncation, not the next episode's reset observation.
"""
import math


def gae(rewards, values, next_values, elapsed_rounds, terminated, truncated,
        gamma=0.995, lam=0.97):
    n = len(rewards)
    if any(len(x) != n for x in
           (values, next_values, elapsed_rounds, terminated, truncated)):
        raise ValueError("transition arrays differ in length")
    if not 0 < gamma <= 1 or not 0 <= lam <= 1:
        raise ValueError("invalid discount")
    advantages = [0.0] * n
    carry = 0.0
    for i in reversed(range(n)):
        dt = elapsed_rounds[i]
        if (not isinstance(dt, int) or isinstance(dt, bool) or dt < 0
                or (dt == 0 and not terminated[i])):
            raise ValueError("elapsed rounds must be positive, or zero at a true terminal boundary")
        if terminated[i] and truncated[i]:
            raise ValueError("a transition cannot be terminal and truncated")
        if not all(math.isfinite(float(x[i])) for x in (rewards, values, next_values)):
            raise ValueError("nonfinite reward/value")
        discount = gamma ** dt
        bootstrap = 0.0 if terminated[i] else next_values[i]
        delta = rewards[i] + discount * bootstrap - values[i]
        continuation = not (terminated[i] or truncated[i])
        carry = delta + (gamma * lam) ** dt * carry * continuation
        advantages[i] = carry
    return advantages, [a + v for a, v in zip(advantages, values)]
