# 🍕 Pizza Dough – Calculator

This is an interactive Pizza dough calculator based on streamlit for you home-pizza oven (Oni, Tenekker, ...). You define which types of eaters you have and what hydration level you want. Based on that dough recipe is calculated automatically.

## Functionality

- 4 eater types: Little, Normal, Much, "Gabriel"
- Hydration level adjustable in 5% steps
- Calculates recipe
- Shows you number of pizzas and possible rest

## Streamlit
[Pizza-Dough-Wizard](https://pizza-dough-wizzard.streamlit.app)

## Installation and run app

   ```bash
   git clone https://github.com/TimRehbronn/Pizza-Dough-Wizzard
   cd pizza-dough-app
   pip install -r requirements.txt
   streamlit run app.py
   http://localhost:8501
   ```

----

Idea: Gabriel Salzburg, Tim Rehbronn \
Code author is Tim Rehbronn \
Created with support of GPT5

# 🍕 Pizza Dough – Calculator

An interactive Streamlit app for home pizza (e.g., Ooni, Tenneker, …). Choose eater types and dough hydration; the app calculates flour, water, yeast, salt, total pizzas, and leftovers. Includes Dark/Light theme, German/English, and an Expert Mode.

## Features
- **Eater types:** Light (0.5), Normal (1.0), Heavy (1.5) — plus **Gabriel** (eats all leftovers → leftovers shown as 0, dough amount unchanged)
- **Hydration:** 50–100% in 5% steps
- **Recipe base:** per 1 kg flour (at 60% hydration): 600 ml water, 7 g yeast, 32 g salt → 6 small pizzas (≈273.17 g each)
- **Calculations:** flour, water, yeast, salt, total pizzas (rounded up to whole pizzas), leftovers (or 0 with Gabriel)
- **Languages:** **Deutsch / English** (toggle in the sidebar)
- **Theme:** **Light / Dark** (toggle in the sidebar)
- **Expert Mode:**
  - Edit eater types and their factors
  - Edit recipe parameters (yeast/salt per kg flour)
  - Edit reference weight per standard pizza (normal eater)
  - Import/Export configuration as JSON
- **Responsive UI** (desktop, laptop, tablet, phone)

## Installation & Run
```bash
# (optional) create and activate a virtual env
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

# install dependencies
pip install -r requirements.txt

# run the app (use streamlit runner, not `python app.py`)
python -m streamlit run app.py
# then open http://localhost:8501 if it does not open automatically
```

## Notes
- The app prints **Starting App…** and **…App started successfully. Visit locally at: http://localhost:8501** in the terminal once loaded.
- Results are approximate; density differences in flour/water may cause slight deviations.

---
Idea: Gabriel Salzburg, Tim Rehbronn  \
Code: Tim Rehbronn  \
Built with the help of GPT‑5
