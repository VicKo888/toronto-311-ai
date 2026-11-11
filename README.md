# Toronto 311 Assistant — Streamlit + Toronto Open Data

A Streamlit prototype that discovers and loads Toronto's public 311 Service Requests - Customer Initiated dataset through the City's CKAN API.

## Run locally
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository and push this project.
2. Visit https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**.
4. Select your repository, branch, and `streamlit_app.py`.
5. Deploy.

Community Cloud installs packages listed in `requirements.txt`.

## Data connection
The app calls Toronto's public CKAN `package_show` endpoint to discover the latest available annual ZIP resource, downloads that resource, and reads the CSV/Excel file from the archive. No API key is configured in this starter.

CKAN endpoint:
`https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=311-service-requests-customer-initiated`

The app caches the downloaded and prepared data for 24 hours. If the City changes the package structure or file schema, inspect the source columns and update `src/toronto_data.py`.

## Important data limitations
- The public dataset contains structured service-request fields, not original free-text resident narratives.
- It is historical data, not a live request-status API.
- It does not submit requests to the City.
- A service type's historical division is not a guarantee of current routing.
- The dataset represents only the records published by the City; it should not be treated as all 311 contacts or all municipal work.
- Synthetic resident messages must be created and reviewed separately for language-model training and evaluation.

## Files
- `streamlit_app.py`: resident UI and data views
- `src/toronto_data.py`: CKAN discovery, download, parsing and normalization
- `src/chat_logic.py`: simple keyword-based baseline for the chat
- `requirements.txt`: deployment dependencies
