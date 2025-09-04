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
        self.a_strategy = 'TitForTat - Cooperate'
        self.b_strategy = 'TitForTat - Cooperate'
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
        elif strategy == 'TitForTat - Cooperate':
            if is_first:
                return 'Cooperate'
            return opponent_last_move
        elif strategy == 'TFT - Defect':
            if is_first:
                return 'Defect'
            return opponent_last_move
        elif strategy == 'Random':
            return random.choice(['Cooperate', 'Defect'])
        else:
            raise ValueError("Unknown strategy")

    def simulate_round(self, a_move, b_move, resolve_congestion=False, drop_coastal=False, apply_noise=False):
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
        net_a_gain = raw_a_gain + a_adjust
        net_b_gain = raw_b_gain + b_adjust
        old_a = self.a_volume
        self.a_volume += net_a_gain
        excess_a = max(0, self.a_volume - self.a_max_capacity)
        self.a_volume = self.a_max_capacity if excess_a > 0 else self.a_volume
        if excess_a > 0 and a_move == 'Cooperate' and b_move == 'Cooperate':
            self.b_volume += excess_a * 0.5  # Spillover to B
        self.b_volume += net_b_gain
        self.b_volume = min(max(self.b_volume, 0), self.b_max_capacity)
        return raw_a_gain, raw_b_gain, net_a_gain, net_b_gain

    def run_simulation(self, resolve_congestion=False, drop_coastal=False, apply_noise=False):
        a_last_move = None
        b_last_move = None
        self.history = []
        for r in range(self.rounds):
            is_first = r == 0
            a_move = self.get_move(self.a_strategy, b_last_move, is_first)
            b_move = self.get_move(self.b_strategy, a_last_move, is_first)
            raw_a_gain, raw_b_gain, net_a_gain, net_b_gain = self.simulate_round(a_move, b_move, resolve_congestion, drop_coastal, apply_noise)
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

level = st.selectbox("Complexity Level", ['Basic', 'Medium', 'Advanced', 'Master'], help="Start with Basic, progress for more features.")

st.markdown("""
This simulation models terminal competition as PD. Adjust level for depth.
""")

with st.expander("Strategy Explanations"):
    st.markdown("""
    - **TitForTat - Cooperate**: Starts cooperate, mirrors last.
    - **TFT - Defect**: Starts defect, mirrors last.
    - **AlwaysCooperate**: Always cooperates.
    - **AlwaysDefect**: Always defects.
    - **Random**: Random each round.
    """)

initial_a = st.number_input("Initial A Volume (TEUs)", value=50000)
initial_b = st.number_input("Initial B Volume (TEUs)", value=20000)
rounds = st.slider("Rounds (Months)", 1, 20, 10)
a_strat = st.selectbox("Terminal A Strategy", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'])
b_strat = st.selectbox("Terminal B Strategy", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'])

if level in ['Medium', 'Advanced', 'Master']:
    resolve_cong = st.checkbox("Resolve Export Congestion? (No Penalty)", value=False)
    drop_coast = st.checkbox("Drop Coastal Contract? (No Penalty)", value=False)

if level in ['Advanced', 'Master']:
    scenario = st.selectbox("Load Scenario (Optional)", ['None', 'Regulatory Clampdown', 'Board Intervention (Googly)', 'Aggressive Poaching'])

allow_mid_change = st.checkbox("Allow Mid-Sim Strategy Change? (Interactive Only)", value=False) if level in ['Advanced', 'Master'] else False

mode = st.radio("Simulation Mode", ['Batch (All Rounds at Once)', 'Interactive (Step-by-Step)'] if level != 'Basic' else ['Batch (All Rounds at Once)'])

if 'runs' not in st.session_state:
    st.session_state.runs = []

tab1, tab2, tab3 = st.tabs(["Simulation", "Reflection Questions", "Comparison"])

with tab1:
    apply_noise = (scenario == 'Regulatory Clampdown') if 'scenario' in locals() else False
    if mode == 'Batch (All Rounds at Once)':
        if st.button("Run Simulation"):
            sim = TerminalSimulation(initial_a_volume=initial_a, initial_b_volume=initial_b, rounds=rounds)
            sim.set_strategies(a_strat, b_strat)
            history, final_a, final_b = sim.run_simulation(resolve_congestion=resolve_cong if 'resolve_cong' in locals() else False, drop_coastal=drop_coast if 'drop_coast' in locals() else False, apply_noise=apply_noise)
            st.write(f"Final Volumes: Terminal A: {final_a} TEUs, Terminal B: {final_b} TEUs")
            
            # Display history table
            df = pd.DataFrame(history)
            st.dataframe(df)
            
            # Chart volumes over rounds
            chart_data = df.melt(id_vars=['round'], value_vars=['a_volume', 'b_volume', 'a_volume'], var_name='Terminal', value_name='Volume')
            chart = alt.Chart(chart_data).mark_line().encode(x='round', y='Volume', color='Terminal').interactive()
            st.altair_chart(chart, use_container_width=True)
            
            # Store run
            st.session_state.runs.append({'A Strategy': a_strat, 'B Strategy': b_strat, 'Final A': final_a, 'Final B': final_b, 'Total Gain': final_a + final_b - initial_a - initial_b})

    else:
        if 'sim' not in st.session_state or st.button("Reset Interactive Mode"):
            st.session_state.sim = TerminalSimulation(initial_a_volume=initial_a, initial_b_volume=initial_b, rounds=rounds)
            st.session_state.sim.set_strategies(a_strat, b_strat)
            st.session_state.current_round = 0
            st.session_state.history = []
            st.session_state.a_last_move = None
            st.session_state.b_last_move = None
            st.session_state.run_complete = False

        if allow_mid_change:
            a_strat = st.selectbox("Update A Strategy (Mid-Sim)", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], key="mid_a")
            b_strat = st.selectbox("Update B Strategy (Mid-Sim)", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], key="mid_b")
            if st.button("Apply Mid-Sim Changes"):
                st.session_state.sim.set_strategies(a_strat, b_strat)

        if st.button("Advance Next Round") and not st.session_state.run_complete:
            sim = st.session_state.sim
            current_round = st.session_state.current_round
            if current_round < sim.rounds:
                is_first = current_round == 0
                a_move = sim.get_move(sim.a_strategy, st.session_state.b_last_move, is_first)
                b_move = sim.get_move(sim.b_strategy, st.session_state.a_last_move, is_first)
                raw_a_gain, raw_b_gain, net_a_gain, net_b_gain = sim.simulate_round(a_move, b_move, resolve_cong if 'resolve_cong' in locals() else False, drop_coast if 'drop_coast' in locals() else False, apply_noise)
                st.session_state.history.append({
                    'round': current_round + 1,
                    'a_move': a_move,
                    'b_move': b_move,
                    'raw_a_gain': raw_a_gain,
                    'raw_b_gain': raw_b_gain,
                    'net_a_gain': net_a_gain,
                    'net_b_gain': net_b_gain,
                    'a_volume': sim.a_volume,
                    'b_volume': sim.b_volume
                })
                st.session_state.a_last_move = a_move
                st.session_state.b_last_move = b_move
                st.session_state.current_round += 1

                # Display current history
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df)

                # Chart
                chart_data = df.melt(id_vars=['round'], value_vars=['a_volume', 'b_volume'], var_name='Terminal', value_name='Volume')
                chart = alt.Chart(chart_data).mark_line().encode(x='round', y='Volume', color='Terminal').interactive()
                st.altair_chart(chart, use_container_width=True)

                if st.session_state.current_round == sim.rounds:
                    st.session_state.run_complete = True
                    st.write(f"Final Volumes: Terminal A: {sim.a_volume} TEUs, Terminal B: {sim.b_volume} TEUs")
                    # Store run
                    st.session_state.runs.append({'A Strategy': a_strat, 'B Strategy': b_strat, 'Final A': sim.a_volume, 'Final B': sim.b_volume, 'Total Gain': sim.a_volume + sim.b_volume - initial_a - initial_b})

with tab2:
    st.markdown("### Post-Simulation Questions")
    st.text_area("1. Based on results, should Terminal A cooperate with B? Why?", help="Consider risks like collusion or price wars from the case.")
    st.text_area("2. If dropping coastal led to gains, quantify short-term loss vs. long-term profitability.", help="Reference case metrics like 2,200 INR/TEU tariff.")

with tab3:
    if st.session_state.runs:
        comp_df = pd.DataFrame(st.session_state.runs)
        st.dataframe(comp_df)
        
        # Bar graph for comparison
        chart_data = comp_df.melt(id_vars=['A Strategy', 'B Strategy'], value_vars=['Final A', 'Final B'], var_name='Terminal', value_name='Volume')
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('A Strategy:N', axis=alt.Axis(labelAngle=-45)),
            y='Volume:Q',
            color='Terminal:N',
            column='B Strategy:N',
            tooltip=['A Strategy', 'B Strategy', 'Terminal', 'Volume']
        ).properties(width=200)
        st.altair_chart(chart, use_container_width=True)
        
        csv = comp_df.to_csv()
        st.download_button("Download Comparison", csv, "runs.csv")

    if st.button("Reset Runs"):
        st.session_state.runs = []

st.markdown("---")
st.markdown("Copyright - Capt. Ramji S Krishnan, Sloan Fellow, London Business School")
