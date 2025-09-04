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
        self.payoffs = {
            ('Cooperate', 'Cooperate'): (5000, 2000),  # A stabilizes/gains moderately, B grows steadily
            ('Cooperate', 'Defect'): (-5000, 10000),   # B poaches heavily from A
            ('Defect', 'Cooperate'): (10000, -5000),   # A counters by poaching or undercutting
            ('Defect', 'Defect'): (-2000, -2000)       # Price war/ mutual aggression hurts both
        }
        self.coastal_impact = -2000  # Penalty if A retains coastal contract (unproductive moves)
        self.congestion_impact = -3000  # Penalty if export bottlenecks not resolved

    def set_strategies(self, a_strat, b_strat):
        """Set strategies for A and B. Options: 'TitForTat', 'AlwaysCooperate', 'AlwaysDefect', 'Random'."""
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

    def simulate_round(self, a_move, b_move):
        a_gain, b_gain = self.payoffs.get((a_move, b_move), (0, 0))
        self.a_volume += a_gain
        self.b_volume += b_gain
        return a_gain, b_gain

    def run_simulation(self, resolve_congestion=False, drop_coastal=False):
        """
        Run the simulation.
        - resolve_congestion: If True, no congestion penalty (A implements TAS/VDTW).
        - drop_coastal: If True, no coastal penalty (A sheds the contract).
        Returns: history (list of dicts), final_a_volume, final_b_volume
        """
        a_last_move = None
        b_last_move = None
        self.history = []  # Reset history
        for r in range(self.rounds):
            is_first = r == 0
            a_move = self.get_move(self.a_strategy, b_last_move, is_first)
            b_move = self.get_move(self.b_strategy, a_last_move, is_first)
            a_gain, b_gain = self.simulate_round(a_move, b_move)
            self.history.append({
                'round': r + 1,
                'a_move': a_move,
                'b_move': b_move,
                'a_gain': a_gain,
                'b_gain': b_gain,
                'a_volume': self.a_volume,
                'b_volume': self.b_volume
            })
            a_last_move = a_move
            b_last_move = b_move
        
        # Apply penalties (scaled by rounds/10 for monthly impact)
        penalty_factor = self.rounds / 10
        if not resolve_congestion:
            self.a_volume += self.congestion_impact * penalty_factor
        if not drop_coastal:
            self.a_volume += self.coastal_impact * penalty_factor
        
        return self.history, self.a_volume, self.b_volume

st.title("Terminal Competition Simulation (Iterated Prisoner's Dilemma)")

# UI Inputs
initial_a = st.number_input("Initial A Volume (TEUs)", value=50000)
initial_b = st.number_input("Initial B Volume (TEUs)", value=20000)
rounds = st.slider("Rounds (Months)", 1, 20, 10)
a_strat = st.selectbox("Terminal A Strategy", ['TitForTat', 'AlwaysCooperate', 'AlwaysDefect', 'Random'])
b_strat = st.selectbox("Terminal B Strategy", ['TitForTat', 'AlwaysCooperate', 'AlwaysDefect', 'Random'])
resolve_cong = st.checkbox("Resolve Export Congestion? (No Penalty)", value=False)
drop_coast = st.checkbox("Drop Coastal Contract? (No Penalty)", value=False)

if st.button("Run Simulation"):
    sim = TerminalSimulation(initial_a_volume=initial_a, initial_b_volume=initial_b, rounds=rounds)
    sim.set_strategies(a_strat, b_strat)
    history, final_a, final_b = sim.run_simulation(resolve_congestion=resolve_cong, drop_coastal=drop_coast)
   
    st.write(f"Final Volumes: Terminal A: {final_a} TEUs, Terminal B: {final_b} TEUs")
   
    # Display history table
    df = pd.DataFrame(history)
    st.dataframe(df)
   
    # Chart volumes over rounds
    chart_data = df.melt(id_vars=['round'], value_vars=['a_volume', 'b_volume'], var_name='Terminal', value_name='Volume')
    chart = alt.Chart(chart_data).mark_line().encode(x='round', y='Volume', color='Terminal').interactive()
    st.altair_chart(chart, use_container_width=True)