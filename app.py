# app.py - Save as app.py and run with Streamlit
import streamlit as st
import random
import pandas as pd
import altair as alt
import json

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

    def simulate_round(self, a_move, b_move, resolve_congestion=False, drop_coastal=False, apply_noise=False, berth_pooling=False, bertrand_mode=False, stackelberg_leader=None):
        raw_a_gain, raw_b_gain = self.payoffs.get((a_move, b_move), (0, 0))
        if bertrand_mode:
            raw_a_gain *= 0.5  # Decay to simulate price convergence
            raw_b_gain *= 0.5
        if berth_pooling and a_move == 'Cooperate' and b_move == 'Cooperate':
            raw_a_gain *= 1.1  # 10% increase due to pooling
            raw_b_gain *= 1.1
        a_adjust = 0
        b_adjust = 0
        if apply_noise:
            a_adjust += random.randint(-500, 500)
            b_adjust += random.randint(-500, 500)
        if not resolve_congestion:
            a_adjust += self.congestion_impact_per_round
        if not drop_coastal:
            a_adjust += self.coastal_impact_per_round
        net_a_gain = int(raw_a_gain + a_adjust)  # Round to whole
        net_b_gain = int(raw_b_gain + b_adjust)  # Round to whole
        old_a = self.a_volume
        self.a_volume += net_a_gain
        excess_a = max(0, self.a_volume - self.a_max_capacity)
        self.a_volume = min(max(self.a_volume, 0), self.a_max_capacity)
        if excess_a > 0 and a_move == 'Cooperate' and b_move == 'Cooperate':
            self.b_volume += int(excess_a * 0.5)  # Spillover rounded
        self.b_volume += net_b_gain
        self.b_volume = min(max(self.b_volume, 0), self.b_max_capacity)
        return raw_a_gain, raw_b_gain, net_a_gain, net_b_gain

    def run_simulation(self, resolve_congestion=False, drop_coastal=False, apply_noise=False, berth_pooling=False, bertrand_mode=False, stackelberg_leader=None):
        a_last_move = None
        b_last_move = None
        self.history = []
        for r in range(self.rounds):
            is_first = r == 0
            a_move = self.get_move(self.a_strategy, b_last_move, is_first)
            b_move = self.get_move(self.b_strategy, a_last_move, is_first)
            raw_a_gain, raw_b_gain, net_a_gain, net_b_gain = self.simulate_round(a_move, b_move, resolve_congestion, drop_coastal, apply_noise, berth_pooling, bertrand_mode, stackelberg_leader)
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

level = st.selectbox("Complexity Level", ['Basic', 'Medium', 'Advanced', 'Master'], help="Basic: Core PD. Medium: Resolutions. Advanced: Scenarios. Master: Advanced models like Bertrand/Stackelberg.")

st.markdown("""
This simulation models terminal competition as PD. Adjust level for depth.
""")

with st.expander("Strategy Explanations (Click to Expand)"):
    st.markdown("""
    - **TitForTat - Cooperate**: Starts by cooperating but mirrors the opponent's last move. Encourages mutual cooperation but retaliates against defection. (Case tie-in: Balanced approach for exploring limited synergies without being exploited.)
    - **TFT - Defect**: Starts by defecting but mirrors the opponent's last move. Often leads to mutual destruction but can test aggression. (Case tie-in: Models potential initial poaching.)
    - **AlwaysCooperate**: Always chooses to cooperate, regardless of the opponent. Risks exploitation but can stabilize if the other follows suit. (Case tie-in: Like board intervention forcing volume retention, potentially leading to mutual benefits or heavy losses.)
    - **AlwaysDefect**: Always chooses to defect, aiming for short-term gains via poaching. Often leads to mutual destruction in iterated games. (Case tie-in: Models Terminal B's aggressive poaching strategy.)
    - **Random**: Chooses cooperate or defect randomly each round. Introduces uncertainty, simulating unpredictable market behaviors.
    """)

initial_a = st.number_input("Initial A Volume (TEUs)", value=50000, help="Starting monthly throughput for Terminal A (established terminal facing decline; default 50,000 TEUs from case; adjust to simulate scenarios like pre-poaching levels or higher capacity).")
initial_b = st.number_input("Initial B Volume (TEUs)", value=20000, help="Starting monthly throughput for Terminal B (new entrant ramping up; default 20,000 TEUs from case; adjust to test aggressive growth or lower entry).")
rounds = st.slider("Rounds (Months)", 1, 20, 10, help="Number of simulation rounds, each representing a month of competition; longer runs highlight long-term effects like sustained cooperation or destructive wars (default 10 for balanced testing).")
a_strat = st.selectbox("Terminal A Strategy", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], help="Select Terminal A's (Priya's) strategy; see expander for details on how each behaves in the PD framework and ties to case dilemmas like counter-poaching or board pressures.")
b_strat = st.selectbox("Terminal B Strategy", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], help="Select Terminal B's (rival's) strategy; e.g., 'AlwaysDefect' for heavy poaching as in the case; see expander for explanations and case ties like aggressive coastal targeting.")

resolve_cong = st.checkbox("Resolve Export Congestion? (No Penalty)", value=False, help="Check to simulate Terminal A resolving export bottlenecks (e.g., via advanced TAS/VDTW system for peak 3 PM–2 AM truck flows, uncoordinated CFS releases). Avoids -300 TEU/round penalty; improves TTT from 60-90 min to 30-45 min, reduces yard congestion, and restores reliability—critical for countering poaching but requires stakeholder coordination and may face implementation challenges.") if level in ['Medium', 'Advanced', 'Master'] else False
drop_coast = st.checkbox("Drop Coastal Contract? (No Penalty)", value=False, help="Check to simulate Terminal A shedding the legacy coastal contract (1 vessel/week, 2,000 TEUs/voyage at reduced tariff 2,200 INR/TEU vs. 3,600 foreign; 10-12 days free import storage, 4-5 export, unproductive moves at 15-20% eRTG capacity). Avoids -200 TEU/round penalty; frees yard space (20-25% occupancy relief), cuts maintenance strain, boosts profitability, but risks short-term volume loss (~2k TEUs), Port Authority backlash, and stakeholder dissatisfaction (consignees/shippers).") if level in ['Medium', 'Advanced', 'Master'] else False

scenario = st.selectbox("Load Scenario (Optional)", ['None', 'Regulatory Clampdown', 'Board Intervention (Googly)', 'Aggressive Poaching'], help="Pre-set parameters based on case 'What Ifs' for quick testing; 'Regulatory Clampdown' adds noise for uncertainty in regulations (e.g., stricter coastal cargo rules increasing costs/flexibility limits—tests response to new risks like contract decisions); 'Board Intervention (Googly)' forces A to AlwaysCooperate (unexpected directive to retain all volume, including coastal, for market share/reputation—conflicts with operational realities, risks volume-at-any-cost strategy); 'Aggressive Poaching' sets B to AlwaysDefect (B aggressively targets volumes, including coastal, testing A's retaliation—highlights destructive wars if not countered).") if level in ['Advanced', 'Master'] else 'None'

if scenario == 'Board Intervention (Googly)':
    if a_strat not in ['AlwaysCooperate', 'TitForTat - Cooperate']:
        st.warning("Board Intervention scenario recommends A to AlwaysCooperate or TitForTat - Cooperate for volume retention—current strategy may not fit; adjust for accurate modeling.")
elif scenario == 'Aggressive Poaching':
    if b_strat != 'AlwaysDefect':
        st.warning("Aggressive Poaching scenario recommends B to AlwaysDefect for heavy poaching—current strategy may not fit; adjust for accurate modeling.")

bertrand_mode = st.checkbox("Enable Bertrand Pricing Mode?", value=False, help="Simulates price competition where gains decay toward marginal cost (e.g., undercutting leads to near-zero profits)—ties to case's tariff wars but clashes with PD's positive synergies if not compared carefully; use for advanced analysis of destructive pricing.") if level == 'Master' else False
stackelberg_leader = st.selectbox("Stackelberg Leader", ['None', 'A', 'B'], help="Enables sequential play: Leader commits first, follower reacts—models commitment advantage (e.g., A as established leader dropping coastal); use for master-level exploration of asymmetric strategies.") if level == 'Master' else 'None'
berth_pooling = st.checkbox("Enable Berth Pooling (10% Increase in Cooperate Gains)", value=False, help="Simulates cooperative berth pooling, adding 10% to gains in mutual cooperate—models reduced queuing, enhanced crane productivity, and capacity boost (10-30% overall); ties to case's conclusion on synergies but assumes trust and regulatory approval.") if level == 'Master' else False

allow_mid_change = st.checkbox("Allow Mid-Sim Strategy Change? (Interactive Only)", value=False, help="Check to enable updating strategies during interactive mode (after some rounds); models adaptive responses like Priya shifting tactics mid-competition, but may disrupt pure strategy analysis—use for 'what if' explorations of changing market conditions.") if level in ['Medium', 'Advanced', 'Master'] else False

mode = st.radio("Simulation Mode", ['Batch (All Rounds at Once)', 'Interactive (Step-by-Step)'] if level != 'Basic' else ['Batch (All Rounds at Once)'], help="Batch: Runs all rounds automatically for quick overview and comparison. Interactive: Advance step-by-step for hands-on control, mid-sim adjustments if enabled, and detailed round-by-round analysis.")

if 'runs' not in st.session_state:
    st.session_state.runs = []

tab1, tab2, tab3 = st.tabs(["Simulation", "Reflection Questions", "Comparison"])

with tab1:
    apply_noise = (scenario == 'Regulatory Clampdown')
    if mode == 'Batch (All Rounds at Once)':
        if st.button("Run Simulation"):
            sim = TerminalSimulation(initial_a_volume=initial_a, initial_b_volume=initial_b, rounds=rounds)
            sim.set_strategies(a_strat, b_strat)
            history, final_a, final_b = sim.run_simulation(resolve_congestion=resolve_cong, drop_coastal=drop_coast, apply_noise=apply_noise, berth_pooling=berth_pooling, bertrand_mode=bertrand_mode)
            st.write(f"Final Volumes: Terminal A: {final_a} TEUs, Terminal B: {final_b} TEUs")
            
            # Display history table without index
            df = pd.DataFrame(history)
            st.dataframe(df.style.hide(axis="index"), column_config={
                'raw_a_gain': st.column_config.NumberColumn(help="Raw gain for A before adjustments/penalties/noise/spillover—base from move (e.g., +2500 for cooperate; changes per row if pooling/Bertrand apply)."),
                'raw_b_gain': st.column_config.NumberColumn(help="Raw gain for B before adjustments—base from move (e.g., +1000 for cooperate; changes per row if pooling/Bertrand apply)."),
                'net_a_gain': st.column_config.NumberColumn(help="Net gain for A after penalties/noise (e.g., raw + adjustments); shows impact of resolutions—changes per row if noise/penalties apply."),
                'net_b_gain': st.column_config.NumberColumn(help="Net gain for B after adjustments; changes per row if noise applies."),
                'total_gain': st.column_config.NumberColumn(help="Combined net gain for A and B this round; highlights mutual benefits or losses—changes per row based on strategies/penalties.")
            })
            
            # Chart volumes over rounds
            chart_data = df.melt(id_vars=['round'], value_vars=['a_volume', 'b_volume'], var_name='Terminal', value_name='Volume')
            chart = alt.Chart(chart_data).mark_line().encode(x='round', y='Volume', color='Terminal').interactive()
            st.altair_chart(chart, use_container_width=True)
            
            # Store run for comparison
            st.session_state.runs.append({'A Strategy': a_strat, 'B Strategy': b_strat, 'Final A': final_a, 'Final B': final_b, 'Total Gain A': final_a - initial_a, 'Total Gain B': final_b - initial_b, 'Total Gain': (final_a + final_b) - (initial_a + initial_b)})

    else:
        if 'sim' not in st.session_state or st.button("Reset Interactive Mode"):
            st.session_state.sim = TerminalSimulation(initial_a_volume=initial_a, initial_b_volume=initial_b, rounds=rounds)
            st.session_state.sim.set_strategies(a_strat, b_strat)
            st.session_state.current_round = 0
            st.session_state.history = []
            st.session_state.a_last_move = None
            st.session_state.b_last_move = None
            st.session_state.run_complete = False

        if allow_mid_change and not st.session_state.run_complete:
            new_a_strat = st.selectbox("Update A Strategy (Mid-Sim)", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], key="mid_a")
            new_b_strat = st.selectbox("Update B Strategy (Mid-Sim)", ['TitForTat - Cooperate', 'TFT - Defect', 'AlwaysCooperate', 'AlwaysDefect', 'Random'], key="mid_b")
            if st.button("Apply Mid-Sim Changes"):
                st.session_state.sim.set_strategies(new_a_strat, new_b_strat)
                a_strat = new_a_strat
                b_strat = new_b_strat

        if st.button("Advance Next Round") and not st.session_state.run_complete:
            sim = st.session_state.sim
            current_round = st.session_state.current_round
            if current_round < sim.rounds:
                is_first = current_round == 0
                a_move = sim.get_move(sim.a_strategy, st.session_state.b_last_move, is_first)
                b_move = sim.get_move(sim.b_strategy, st.session_state.a_last_move, is_first)
                raw_a_gain, raw_b_gain, net_a_gain, net_b_gain = sim.simulate_round(a_move, b_move, resolve_cong, drop_coast, apply_noise, berth_pooling, bertrand_mode)
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

                # Display current history without index
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df.style.hide(axis="index"), column_config={
                    'raw_a_gain': st.column_config.NumberColumn(help="Raw gain for A before adjustments/penalties/noise/spillover—base from move (e.g., +2500 for cooperate; changes per row if pooling/Bertrand apply)."),
                    'raw_b_gain': st.column_config.NumberColumn(help="Raw gain for B before adjustments—base from move (e.g., +1000 for cooperate; changes per row if pooling/Bertrand apply)."),
                    'net_a_gain': st.column_config.NumberColumn(help="Net gain for A after penalties/noise (e.g., raw + adjustments); shows impact of resolutions—changes per row if noise/penalties apply."),
                    'net_b_gain': st.column_config.NumberColumn(help="Net gain for B after adjustments; changes per row if noise applies."),
                    'total_gain': st.column_config.NumberColumn(help="Combined net gain for A and B this round; highlights mutual benefits or losses—changes per row based on strategies/penalties.")
                })

                # Chart
                chart_data = df.melt(id_vars=['round'], value_vars=['a_volume', 'b_volume'], var_name='Terminal', value_name='Volume')
                chart = alt.Chart(chart_data).mark_line().encode(x='round', y='Volume', color='Terminal').interactive()
                st.altair_chart(chart, use_container_width=True)

                if st.session_state.current_round == sim.rounds:
                    st.session_state.run_complete = True
                    st.write(f"Final Volumes: Terminal A: {sim.a_volume} TEUs, Terminal B: {sim.b_volume} TEUs")
                    # Store run
                    st.session_state.runs.append({'A Strategy': a_strat, 'B Strategy': b_strat, 'Final A': sim.a_volume, 'Final B': sim.b_volume, 'Total Gain A': sim.a_volume - initial_a, 'Total Gain B': sim.b_volume - initial_b, 'Total Gain': (sim.a_volume + sim.b_volume) - (initial_a + initial_b)})

with tab2:
    st.markdown("### Post-Simulation Questions")
    q1 = st.text_area("1. Based on results, should Terminal A cooperate with B? Why?", help="Consider risks like collusion or price wars from the case; answers are stored in session and can be downloaded.")
    q2 = st.text_area("2. If dropping coastal led to gains, quantify short-term loss vs. long-term profitability.", help="Reference case metrics like 2,200 INR/TEU tariff; answers are stored in session and can be downloaded.")
    if st.button("Save & Download Answers"):
        answers = {'q1': q1, 'q2': q2}
        json_str = json.dumps(answers)
        st.download_button("Download Answers (JSON)", json_str, "answers.json", mime="application/json")

with tab3:
    if st.session_state.runs:
        comp_df = pd.DataFrame(st.session_state.runs)
        st.dataframe(comp_df.style.hide(axis="index"))
        
        # Bar graph for comparison - side-by-side A/B/combined, like attached
        comp_df['Combined Gain'] = comp_df['Total Gain A'] + comp_df['Total Gain B']
        comp_df['Run Label'] = comp_df['A Strategy'] + ' vs ' + comp_df['B Strategy']
        chart_data = comp_df.melt(id_vars=['Run Label'], value_vars=['Total Gain A', 'Total Gain B', 'Combined Gain'], var_name='Payoff Type', value_name='Cumulative Payoff')
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Run Label:N', axis=alt.Axis(labelAngle=-45)),
            y='Cumulative Payoff:Q',
            color='Payoff Type:N',
            tooltip=['Run Label', 'Payoff Type', 'Cumulative Payoff']
        ).properties(width=600, title='Cumulative Payoffs After ' + str(rounds) + ' Rounds')
        st.altair_chart(chart, use_container_width=True)
        
        csv = comp_df.to_csv()
        st.download_button("Download Comparison", csv, "runs.csv")

    if st.button("Reset Runs"):
        st.session_state.runs = []

st.markdown("Copyright - Capt. Ramji S Krishnan, Sloan Fellow, London Business School")
