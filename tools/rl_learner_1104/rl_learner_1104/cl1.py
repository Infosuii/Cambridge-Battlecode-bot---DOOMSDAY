"""Independent CL1 af91 preprocessing and recurrent camp-pointer actor.

Pins the implemented C++ encoder, not the earlier proposal. Teacher-only smoke
until the producer supplies the authoritative field/visibility audit. No IDs,
recorder fuel, v92 claims, primitive outcomes or future rewards enter the actor.
"""
import torch
from torch import nn
from torch.nn import functional as F

PREPROCESS_VERSION = 'jd-cl1-af91-v1'
SOURCE_ENCODER = 'af91bd50a3e655de37ce27f4962e76b7d252965b'
WIDTHS = {'ally': 20, 'enemy': 23, 'camp': 19, 'altar': 4}
GLOBAL_WIDTH = 58


def onehot(x, n):
    valid = (x >= 0) & (x < n)
    return F.one_hot(x.long().clamp(0, n - 1), n).float() * valid.unsqueeze(-1)


def preprocess(raw):
    if raw.ndim != 2 or raw.shape[1] != 448 or raw.is_floating_point():
        raise ValueError('CL1 requires B x 448 integer observations')
    x = raw.float()
    g, s = x[:, :16], x[:, 16:48]
    a = x[:, 48:128].reshape(-1, 5, 16)
    e = x[:, 128:224].reshape(-1, 6, 16)
    c = x[:, 224:416].reshape(-1, 12, 16)
    l = x[:, 416:448].reshape(-1, 4, 8)
    present = {k: z[:, :, 0] > 0 for k, z in [('ally', a), ('enemy', e), ('camp', c), ('altar', l)]}
    # Distances -1 are unknown; numerical zero is accompanied by known flags.
    distances = g[:, 12:14]
    gs = torch.cat((g[:, :7] / g.new_tensor([2000, 1000, 1000, 1000, 6, 256, 256]),
                    onehot(g[:, 7], 3), onehot(g[:, 8], 6), g[:, 9:12] / 6,
                    distances.clamp_min(0) / 256, (distances >= 0).float()), -1)
    bits = ((s[:, 9].long().unsqueeze(-1) >> torch.arange(9, device=x.device)) & 1).float()
    ss = torch.cat((onehot(s[:, 0], 13),
                    s[:, 1:9] / s.new_tensor([256, 256, 1000, 1000, 100, 100, 1000, 1000]),
                    bits, s[:, 10:15] / s.new_tensor([100, 100, 32, 1, 4])), -1)
    visible = a[:, :, 2:3] > 0
    av = a[:, :, 3:9] / a.new_tensor([256, 256, 1000, 256, 100, 32])
    ally = torch.cat((onehot(a[:, :, 1], 13), visible.float(), av * visible), -1)
    enemy = torch.cat((onehot(e[:, :, 1], 13), e[:, :, 2:3],
                       e[:, :, 3:4].clamp_min(0) / 2000, (e[:, :, 3:4] >= 0).float(),
                       e[:, :, 4:11] / e.new_tensor([256, 256, 1000, 1000, 256, 32, 1])), -1)
    camp = torch.cat((c[:, :, 1:10] / c.new_tensor([256, 256, 16, 16, 16, 16, 16, 16, 16]),
                      onehot(c[:, :, 10], 3), (c[:, :, 10:11] >= 0).float(),
                      c[:, :, 11:14] / c.new_tensor([16, 1000, 256]),
                      c[:, :, 14:15].clamp_min(0) / 2000, (c[:, :, 14:15] >= 0).float(),
                      c[:, :, 15:16] / 1000), -1)
    altar = l[:, :, [1, 2, 3, 7]] / l.new_tensor([256, 256, 256, 1])
    entities = dict(ally=ally, enemy=enemy, camp=camp, altar=altar)
    entities = {k: v.masked_fill(~present[k].unsqueeze(-1), 0) for k, v in entities.items()}
    globals_ = torch.cat((gs, ss), -1)
    if globals_.shape[-1] != GLOBAL_WIDTH or any(entities[k].shape[-1] != w for k, w in WIDTHS.items()):
        raise AssertionError('preprocessor width drift')
    return entities, present, globals_


class CampPointer(nn.Module):
    """Permutation-equivariant camp scores, invariant pooled recurrent context.

    Target13 is a hybrid macro milestone; none also includes outside-12 targets.
    It is not a learned full-control bot. PyTorch GRU gate order is r,z,n.
    """
    def __init__(self, enc_width=8, context_width=32, memory_width=16, pointer_width=16):
        super().__init__()
        self.architecture = dict(enc_width=enc_width, context_width=context_width,
                                 memory_width=memory_width, pointer_width=pointer_width)
        if any(not isinstance(v,int) or v < 1 or v > 128 for v in self.architecture.values()):
            raise ValueError('invalid actor dimensions')
        self.names = tuple(sorted(WIDTHS))
        self.encoders = nn.ModuleDict({k: nn.Linear(w, enc_width) for k, w in WIDTHS.items()})
        self.context = nn.Linear(GLOBAL_WIDTH + 2 * enc_width * len(WIDTHS), context_width)
        self.memory = nn.GRUCell(context_width, memory_width)
        self.pointer = nn.Linear(enc_width + memory_width, pointer_width)
        self.score = nn.Linear(pointer_width, 1)
        self.none = nn.Linear(memory_width, 1)

    def initial_state(self, batch):
        return self.none.weight.new_zeros(batch, self.memory.hidden_size)

    def forward(self, raw, hidden, reset):
        entities, present, globals_ = preprocess(raw)
        pooled, encoded = [], {}
        for k in self.names:
            mask = present[k]
            z = torch.relu(self.encoders[k](entities[k]))
            encoded[k] = z
            n = mask.sum(1, keepdim=True)
            mean = (z * mask.unsqueeze(-1)).sum(1) / n.clamp_min(1)
            mx = z.masked_fill(~mask.unsqueeze(-1), -torch.inf).max(1).values
            pooled += [mean, torch.where(n > 0, mx, torch.zeros_like(mx))]
        ctx = torch.relu(self.context(torch.cat(pooled + [globals_], -1)))
        h = self.memory(ctx, hidden * (~reset.bool()).unsqueeze(-1))
        per_camp = torch.cat((encoded['camp'], h[:, None, :].expand(-1, 12, -1)), -1)
        scores = self.score(torch.tanh(self.pointer(per_camp))).squeeze(-1)
        logits = torch.cat((scores, self.none(h)), -1)
        mask = torch.cat((present['camp'], torch.ones_like(present['camp'][:, :1])), -1)
        return logits.masked_fill(~mask, -torch.inf), h
