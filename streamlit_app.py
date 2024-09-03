import datetime
import os
import pandas as pd
import streamlit as st
import altair as alt

# Set the page configuration
st.set_page_config(page_title="Agendamento de Entrega", page_icon="📅")
st.title("📅 Agendamento de Entrega")
st.write(
    """
    Regras gerais para entrega:\n
•	Não acataremos divergências de preços e/ou quantidades (nestes casos emitiremos a NF devolução parcial), ou de prazo e/ou produtos sem cadastro (neste caso realizaremos a recusa total da NF); \n
•	No ato do recebimento das mercadorias, se caso houver avarias, faltas ou inversão de produtos, emitiremos de imediato a nota fiscal de devolução, sem a necessidade de contatar a indústria e entregaremos ao motorista responsável pela entrega. \n
•	O shelf-life para o recebimento de mercadorias é de no mínimo 70% em diante da data de fabricação. Abaixo deste percentual efetuaremos a nota fiscal de devolução destes itens.\n
•	Será cobrado um valor por palete/por tonelada descarregada, de acordo com a tabela: \n
Tipo da carga	Valor unit.\n
Pallet monoproduto	R$ 35,00\n
Pallet misto	R$ 45,00\n
Estivado (por ton.)	R$ 62,00\n
    """
)

# Define the path for the CSV file
csv_file_path = "schedules.csv"

# Load existing schedules from CSV or create a new dataframe
if os.path.exists(csv_file_path):
    df = pd.read_csv(csv_file_path)
else:
    # Create an empty dataframe with the necessary columns
    df = pd.DataFrame(
        columns=["ID", "Fornecedor", "Número da NF", "Drop-off Date", "Drop-off Time", "Status", "Centro de Distribuição", "Tipo de Carga",
                 "Número de Pallets", "Peso Total", "Número de SKUs"])
    df.to_csv(csv_file_path, index=False)  # Save the initial dataframe

# Section to add a new schedule
st.header("Add a New Schedule")

with st.form("add_schedule_form"):
    supplier_name = st.text_input("Fornecedor")
    product = st.text_input("Número da NF")
    dropoff_date = st.date_input("Drop-off Date", min_value=datetime.date.today())
    dropoff_time = st.time_input("Drop-off Time")
    status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"])
    distribution_center = st.selectbox("Centro de Distribuição", ["CLAS", "GPA", "JSL"])
    load_type = st.selectbox("Tipo de Carga", ["Pallet Monoproduto", "Pallet Misto", "Estivado"])
    pallet_number = st.number_input("Número de Pallets", step=1)
    total_weight = st.number_input("Peso Total", step=1)
    sku_number = st.number_input("Número de SKUs", step=1)
    submitted = st.form_submit_button("Submit")

if submitted:
    recent_schedule_id = int(df["ID"].max()[8:]) + 1 if not df.empty else 1
    new_schedule = {
        "ID": f"SCHEDULE-{recent_schedule_id}",
        "Fornecedor": supplier_name,
        "Número da NF": product,
        "Drop-off Date": dropoff_date,
        "Drop-off Time": dropoff_time.strftime("%H:%M"),
        "Status": status,
        "Centro de Distribuição": distribution_center,
        "Tipo de Carga": load_type,
        "Número de Pallets": pallet_number,
        "Peso Total": total_weight,
        "Número de SKUs": sku_number
    }

    df_new = pd.DataFrame([new_schedule])

    st.write("Schedule submitted! Here are the schedule details:")
    st.dataframe(df_new, use_container_width=True, hide_index=True)

    df = pd.concat([df_new, df], axis=0)
    df.to_csv(csv_file_path, index=False)  # Save the updated dataframe

# Section to view and edit existing schedules
st.header("Existing Schedules")
st.write(f"Number of schedules: `{len(df)}`")

st.info(
    "You can edit the schedules by double-clicking on a cell. Note how the plots below "
    "update automatically! You can also sort the table by clicking on the column headers.",
    icon="✍️",
)

edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Schedule status",
            options=["Scheduled", "Completed", "Cancelled"],
            required=True,
        ),
    },
    disabled=["ID", "Fornecedor", "Número da NF", "Drop-off Date", "Drop-off Time"],
)

# Save edits back to CSV
if edited_df is not None:
    df = edited_df
    df.to_csv(csv_file_path, index=False)

# Show some metrics and charts about the schedules
st.header("Statistics")

col1, col2, col3 = st.columns(3)
num_scheduled = len(df[df.Status == "Scheduled"])
col1.metric(label="Number of scheduled drop-offs", value=num_scheduled, delta=5)
col2.metric(label="Completed drop-offs", value=len(df[df.Status == "Completed"]))
col3.metric(label="Cancelled drop-offs", value=len(df[df.Status == "Cancelled"]))

st.write("")
st.write("##### Drop-off status per month")
status_plot = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x="month(Drop-off Date):O",
        y="count():Q",
        xOffset="Status:N",
        color="Status:N",
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### Current drop-off statuses")
status_distribution_plot = (
    alt.Chart(df)
    .mark_arc()
    .encode(theta="count():Q", color="Status:N")
    .properties(height=300)
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(status_distribution_plot, use_container_width=True, theme="streamlit")
