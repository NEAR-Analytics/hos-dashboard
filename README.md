# FIQ Dashboard: Technical Document

## For collaborating

1. Clone the [FIQ-Dashboard Repo](https://github.com/NEAR-Analytics/fiq-dashboard)
2. Create a `.env` file in the root directory and copy the contents from `.env_example`
3. Install uv package manager:
   ```bash
   pip install uv
   ```
4. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   ```
5. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
6. Run the Streamlit app:
   ```bash
   streamlit run Home.py
   ```

NB: If you want to run an ipynb you need to first run uv add --dev ipykernel


## TO DO:

1. Revamp color palette
2. Add Supply and Top Movers
3. Revamp code to generalize
4. Build and host API endpoints
5. use clickhouse restore table. Restore table is a snapshot of categories, the other table is live and dynamic so can influence calculations. Figure out a way to add new arrivals in that cateogry.
6. Bittensor, virtuals, everyone else deep dive
7. Newly launched (not prio) deep dive
8. Add intents data to net flows (prio 1)
9. Add bridges data