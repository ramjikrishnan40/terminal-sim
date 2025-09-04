# app.py - Save as app.py and run with Streamlit
import streamlit as st
import random
import pandas as pd
import altair as alt

class TerminalSimulation:
    def __init__(self, initial_a_volume=50000, initial_b_volume=20000, rounds=10):
        self.a_volume = initial_a_volume
        self.b_volume = initial_b_volume
        self.rounds = rounds
        self.a_strategy = 'TitForTat'
        self.b_strategy = 'TitForTat'
        self.history = []
        self.a_max_capacity = 60000
        self.b_max_capacity = 75000
        self.payoffs = {
            ('Cooperate', 'Cooperate'): (2500, 1000),
            ('Cooperate', 'Defect'): (-5000, 10000),
            ('Defect', 'Cooperate'): (10000, -5000),
            ('Defect', 'Defect'): (-2000, -2000)
        }
        self.coastal_impact_per_round = -200
        self.congestion_impact_per_round = -300

    def set_strategies(self, a_strat, b_strat):
        self.a_strategy = a_strat
        self.b_strategy = b_strat

    def get_move(self, strategy, opponent_last_move, is_first):
        if strategy == 'AlwaysCooperate':
            return 'Cooperate'
        elif strategy == 'AlwaysDefect':
            return 'Defect'
        elif strategy == 'TitForTat':
            if is_first:
                return 'Cooperate'
            return opponent_last_move
        elif strategy == 'Random':
            return random.choice(['Cooperate', 'Defect'])
        else:
            raise ValueError("Unknown strategy")

    def simulate_round(self, a_move, b_move, apply_noise=False, resolve_congestion=False, drop_coastal=False, bertrand_mode=False, stackelberg_leader=None):
        raw_a_gain, raw_b_gain = self.payoffs.get((a_move, b_move), (0, 0))
        a_adjust = 0
        b_adjust = 0
        if apply_noise:
            a_adjust += random.randint(-500, 500)
            b_adjust += random.randint(-500, 500)
        if not resolve_congestion:
            a_adjust += self.congestion_impact_per_round
        if not drop_coastal:
            a_adjust += self.coastal_impact_per_round
        if bertrand_mode:
            # Decay gains toward 0 for price undercutting
            raw_a_gain *= 0.5  # Simulate convergence to marginal cost
            raw_b_gain *= 0.5
        net_a_gain = raw_a_gain + a_adjust
        net_b_gain = raw_b_gain + b_adjust
        self.a_volume += net_a_gain
        self.b_volume += net_b_gain
        self.a_volume = min(max(self.a_volume, 0), self.a_max_capacity)
        self.b_volume = min(max(self.b_volume, 0), self.b_max_capacity)
        return raw_a_gain, raw_b_gain, net_a_gain, net_b_gain

    def run_simulation(self, resolve_congestion=False, drop_coastal=False, apply_noise=False, bertrand_mode=False, stackelberg_leader=None):
        a_last_move = None
        b_last_move = None
        self.history = []
        for r in range(self.rounds):
            is_first = r == 0
            a_move = self.get_move(self.a_strategy, b_last_move, is_first)
            b_move = self.get_move(self.b_strategy, a_last_move, is_first)
            raw_a_gain, raw_b_gain, net_a_gain, net_b_gain = self.simulate_round(a_move, b_move, apply_noise, resolve_congestion, drop_coastal, bertrand_mode, stackelberg_leader)
            self.history.append({
                'round': r + 1,
                'a_move': a_move,
                'b_move': b_move,
                'raw_a_gain': raw_a_gain,
                'raw_b_gain': raw_b_gain,
                'net_a_gain': net_a_gain,
                'net_b_gain': net_b_gain,
                'a_volume': self.a_volume,
                'b_volume': self.b_volume
            })
            a_last_move = a_move
            b_last_move = b_move
        return self.history, self.a_volume, self.b_volume

st.title("Terminal Competition Simulation (Iterated Prisoner's Dilemma)")

level = st.selectbox("Complexity Level", ['Basic', 'Medium', 'Advanced', 'Master'], help="Start with Basic for core PD, progress for more features.")

st.markdown("""
This simulation models terminal competition as PD. Adjust level for depth.
""")

with st.expander("Strategy Explanations"):
    st.markdown(...)  # As before

# Inputs, gated by level
initial_a = st.number_input("Initial A Volume (TEUs)", value=50000, help=... if level == 'Basic' else "Detailed help...")
# Similar for others

if level in ['Medium', 'Advanced', 'Master']:
    resolve_cong = st.checkbox(...) 
    drop_coast = st.checkbox(...)

if level in ['Advanced', 'Master']:
    scenario = st.selectbox(...)
    # Scenario logic as before

if level == 'Master':
    bertrand_mode = st.checkbox("Enable Bertrand Pricing Mode?", help="Simulates price undercutting to marginal cost—gains decay. Discuss case tariff wars.")
    stackelberg_leader = st.selectbox("Stackelberg Leader", ['None', 'A', 'B'], help="Sequential play: Leader commits first, follower reacts. Models commitment advantage.")

mode = st.radio("Simulation Mode", ... if level != 'Basic' else ['Batch'])  # Limit interactive to higher levels

tab1, tab2, tab3 = st.tabs(["Simulation", "Reflection Questions", "Game Guide"])

with tab1:
    # Sim logic as before, passing bertrand_mode, stackelberg_leader to run_simulation

with tab2:
    # Questions, level-specific (e.g., if level=='Master': add "Discuss Bertrand zero profits")

with tab3:
    st.markdown("### Game Guide")
    st.markdown("Basic: PD basics. Medium: Add penalties. Advanced: Scenarios. Master: Bertrand (price to cost, zero profits—clash warning if PD positives expected; discuss differentiation). Stackelberg (sequential—leader gains if commitment credible).")

# Interactive mode adjusted for Stackelberg (e.g., if leader=='A': prompt A move first)
