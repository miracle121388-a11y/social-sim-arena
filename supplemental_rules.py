"""Post-freeze truth-only stress rules; candidate simulator remains sealed.

Copied from SocialSimulator in prepare_and_cache.py SHA256 445e265062656782d3dc3e24201b6a29046391568da42a1ee279d8d5d432a47a.
Only added a stress selector, two-hop propagation and waiting impatience.
No-shift parity is regression tested. Do not use this file for search.
"""
import torch
from prepare_and_cache import N_AGENTS, N_SEEDS, N_STEPS, SocioVerse_Campus


class SupplementalStressSimulator:
    """Tensorized over mechanisms, random seeds and people; loops only time/events.

    State: informed/attempted/booked/waiting, budget, availability, experience.
    Intent is logged before capacity/conflict/budget settlement; forwarding uses
    a ring neighbor's previous state, never global private information.
    """
    def __init__(self, n_agents=N_AGENTS, n_seeds=N_SEEDS, steps=N_STEPS, device='cpu'):
        self.n, self.s, self.t, self.device = n_agents, n_seeds, steps, device

    @torch.no_grad()
    def run(self, theta, events, seed=0, misspecified=False, stress="none"):
        if stress not in {"none", "waiting", "propagation", "both"}:
            raise ValueError("Unknown stress rule")
        theta, events = theta.to(self.device), events.to(self.device)
        m, e = theta.shape[0], len(events)
        if theta.ndim == 2:
            theta = theta[:,None,:].expand(-1,e,-1)
        if theta.shape != (m,e,3):
            raise ValueError('Parameters must be [M,3] shared or [M,E,3] unshared')
        pop = SocioVerse_Campus.population(self.n, seed+71, self.device)
        gen = torch.Generator(device=self.device).manual_seed(seed)
        shape = (m,self.s,e,self.n)
        informed = torch.zeros(shape, dtype=torch.bool, device=self.device)
        attempted = informed.clone(); booked = informed.clone(); waiting = informed.clone()
        attended = informed.clone()
        queued = torch.full(shape, 999., device=self.device)
        budget = pop[:,2].expand(m,self.s,self.n).clone()
        experience = pop[:,3].expand(m,self.s,self.n).clone()
        priority = torch.rand((1,self.s,e,self.n), generator=gen, device=self.device)
        attention = theta[:,:,0][:,None,:,None] * events[:,4][None,None,:,None]
        part = theta[:,:,1][:,None,:,None] * pop[:,0][None,None,None,:]
        dropout = theta[:,:,2][:,None,:,None]
        traces, intents, views = [], [], []
        def random():
            # Common random numbers align mechanisms; independent truth seeds.
            return torch.rand((1,self.s,e,self.n), generator=gen, device=self.device)
        for t in range(self.t):
            window = (t < events[:,6]-1)[None,None,:,None]
            notified = (random() < attention) if t == 0 else torch.zeros_like(informed)
            if t > 0:
                peer = torch.roll(informed | booked, 1, -1)
                if stress in {"propagation", "both"}:
                    peer |= torch.roll(informed | booked, 2, -1)
                propagation = .90 if stress in {"propagation", "both"} else .35
                notified |= peer & (events[:,2][None,None,:,None] > 0) & (random() < attention*propagation)
            newly_seen = notified & ~informed & window
            informed |= newly_seen
            intent = informed & ~attempted & window & (random() < part*(1+.04*experience[:,:,None,:]).clamp_max(1.2))
            # One participation decision after first notice: preserves a*p ambiguity.
            intent &= newly_seen
            attempted |= newly_seen
            cancel = booked & (random() < .035*dropout) & window
            hazard = (dropout + .45).clamp_max(1.) if stress in {"waiting", "both"} and t >= 2 else dropout
            leave = waiting & (random() < hazard) & (t > 0)
            if misspecified and t == 4:
                # Withheld common transport disruption, absent from every candidate.
                cancel |= booked & (random() < .85)
                leave |= waiting
            booked &= ~cancel; waiting &= ~leave
            budget += (cancel.float()*events[:,5][None,None,:,None]).sum(2)
            for j in range(e):
                start = int(events[j,6])
                conflict = torch.zeros_like(budget, dtype=torch.bool)
                if events[j,3] > 0:
                    same_time = (events[:,6] == events[j,6]) & (torch.arange(e,device=self.device) != j)
                    conflict = booked[:,:,same_time,:].any(2)
                eligible = (pop[:,1] > 0) & (budget >= events[j,5]) & ~conflict
                applicants = intent[:,:,j,:] & eligible
                wait_enabled = events[j,1] > 0
                queued[:,:,j,:] = torch.where(applicants, t+priority[:,:,j,:], queued[:,:,j,:])
                pool = (waiting[:,:,j,:] | applicants) & eligible & (t < start-1)
                scores = queued[:,:,j,:].masked_fill(~pool, 1e6)
                order = scores.argsort(dim=-1, stable=True)
                ranks = torch.empty_like(order).scatter_(-1, order, torch.arange(self.n,device=self.device).expand_as(order))
                slots = (events[j,0] - booked[:,:,j,:].sum(-1)).clamp_min(0)
                admit = pool & (ranks < slots[:,:,None])
                booked[:,:,j,:] |= admit
                budget -= admit * events[j,5]
                waiting[:,:,j,:] = (pool & ~admit) & wait_enabled
                if t == start:
                    arrived = booked[:,:,j,:] & (pop[:,1] > 0)
                    attended[:,:,j,:] |= arrived
                    experience += arrived
            assert not (booked & waiting).any()
            assert (booked.sum(-1) <= events[:,0][None,None,:]).all()
            assert (budget >= -1e-5).all()
            traces.append(torch.stack([booked.sum(-1),waiting.sum(-1),attended.sum(-1)],-1))
            intents.append(intent.sum(-1)); views.append(newly_seen.sum(-1))
        return {'Trajectories': torch.stack(traces,3).float()/self.n,
                'Intent': torch.stack(intents,3), 'Views': torch.stack(views,3),
                'Agent': pop, 'Event': events}

