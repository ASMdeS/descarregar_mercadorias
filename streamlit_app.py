import datetime
import os
import pandas as pd
import streamlit as st
import altair as alt
from datetime import time

# Set the page configuration
st.set_page_config(page_title="Agendamento de Entrega", page_icon="📅")
st.title("📅 Agendamento de Entrega")
st.divider()
st.subheader("Regras gerais para entrega")
st.write(
    """
•	Não acataremos divergências de preços e/ou quantidades (nestes casos emitiremos a NF devolução parcial), ou de prazo e/ou produtos sem cadastro (neste caso realizaremos a recusa total da NF). \n
•	No ato do recebimento das mercadorias, se caso houver avarias, faltas ou inversão de produtos, emitiremos de imediato a nota fiscal de devolução, sem a necessidade de contatar a indústria e entregaremos ao motorista responsável pela entrega. \n
•	O shelf-life para o recebimento de mercadorias é de no mínimo 70% em diante da data de fabricação. Abaixo deste percentual efetuaremos a nota fiscal de devolução destes itens.\n
•	Será cobrado um valor por palete/por tonelada descarregada, de acordo com a tabela:
    """
)

dicionario_precos = {
    "Tipo da carga": ["Pallet monoproduto", "Pallet misto", "Estivado (por tonelada)"],
    "Valor unitário": ["R$ 35,00", "R$ 45,00", "R$ 62,00"]
}

# Creating the DataFrame
dataframe_precos = pd.DataFrame(dicionario_precos)
st.table(dataframe_precos)

# Define the path for the CSV file
csv_file_path = "schedules.csv"

# Load existing schedules from CSV or create a new dataframe
if os.path.exists(csv_file_path):
    df = pd.read_csv(csv_file_path)
else:
    # Create an empty dataframe with the necessary columns
    df = pd.DataFrame(
        columns=["ID", "Indústria", "Número da NF", "Drop-off Date", "Drop-off Time", "Status",
                 "Centro de Distribuição", "Tipo de Carga",
                 "Número de Pallets", "Peso Total", "Número de SKUs", "Data de Criação"])
    df.to_csv(csv_file_path, index=False)  # Save the initial dataframe

# Section to add a new schedule
st.header("Adicionar Agendamento")

with st.form("add_schedule_form"):
    supplier_name = st.text_input("Indústria")
    product = st.text_input("Número da NF")
    dropoff_date = st.date_input("Data", min_value=datetime.date.today())
    dropoff_time = st.time_input("Horário")
    status = st.selectbox("Status", ["Agendado", "Completo", "Cancelado"])
    distribution_center = st.selectbox("Centro de Distribuição", ["CLAS", "GPA", "JSL"])
    load_type = st.selectbox("Tipo de Carga", ["Pallet Monoproduto", "Pallet Misto", "Estivado"])
    pallet_number = st.number_input("Número de Pallets", step=1)
    total_weight = st.number_input("Peso Total", step=1)
    sku_number = st.number_input("Número de SKUs", step=1)
    submitted = st.form_submit_button("Enviar")

# Define the maximum number of schedules allowed per day
max_schedules_per_day = 5

# Definindo o horário mínimo e máximo
min_clas = time(7, 0)  # 08:00 AM
max_clas = time(15, 0)  # 06:00 PM

min_jsl = time(13, 30)  # 08:00 AM
max_jsl = time(22, 0)  # 06:00 PM

min_gpa = time(8, 0)  # 08:00 AM
max_gpa = time(15, 0)  # 06:00 PM

if submitted:
    # Check how many schedules are already set for the selected drop-off date
    schedules_on_date = df[(df["Drop-off Date"] == str(dropoff_date)) &
                           (df["Centro de Distribuição"] == distribution_center)]
    if len(schedules_on_date) >= max_schedules_per_day:
        st.error(
            f"Não é possível agendar mais de {max_schedules_per_day} entregas para o dia {dropoff_date} por Centro de Distribuição.")
    elif distribution_center == "CLAS" and (dropoff_time < min_clas or dropoff_time > max_clas):
        st.error(f"É necessário agendar entre às 7hrs e 15hrs")
    elif distribution_center == "JSL" and (dropoff_time < min_jsl or dropoff_time > max_jsl):
        st.error(f"É necessário agendar entre às 13hrs30min e 22hrs")
    elif distribution_center == "GPA" and (dropoff_time < min_gpa or dropoff_time > max_gpa):
        st.error(f"É necessário agendar entre às 8hrs e 15hrs")
    else:
        if df.empty or df.ID.isnull().all():
            recent_schedule_id = 1  # Caso não haja registros anteriores, começar com o ID 1
        else:
            recent_schedule_id = int(max(df.ID).split("-")[1])
        new_schedule = {
            "ID": f"SCHEDULE-{recent_schedule_id + 1}",
            "Indústria": supplier_name,
            "Número da NF": product,
            "Drop-off Date": dropoff_date,
            "Drop-off Time": dropoff_time.strftime("%H:%M"),
            "Status": status,
            "Centro de Distribuição": distribution_center,
            "Tipo de Carga": load_type,
            "Número de Pallets": pallet_number,
            "Peso Total": total_weight,
            "Número de SKUs": sku_number,
            "Data de Criação": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        df_new = pd.DataFrame([new_schedule])

        st.write("Agendamento enviado! Aqui estão os detalhes:")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

        df = pd.concat([df_new, df], axis=0)
        df.to_csv(csv_file_path, index=False)  # Save the updated dataframe

# Section to view and edit existing schedules
st.header("Agendamentos Existentes")
st.write(f"Número de Agendamentos: `{len(df)}`")

# Add a selectbox to filter by Distribution Center
distribution_center_filter = st.selectbox("Filtrar por Centro de Distribuição",
                                          ["Todos"] + df["Centro de Distribuição"].unique().tolist())

# Filter the dataframe based on the selected Distribution Center
if distribution_center_filter != "Todos":
    df = df[df["Centro de Distribuição"] == distribution_center_filter]

st.info(
    "Você pode editar os agendamentos ao clicar duas vezes em uma célula. Perceba como os gráficos "
    "são atualizados automaticamente! Você também pode ordenar a tabela ao clicar no cabeçalho das colunas.",
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
            options=["Agendado", "Completo", "Cancelado"],
            required=True,
        ),
    },
    disabled=["ID", "Indústria", "Número da NF", "Drop-off Date", "Drop-off Time", "Centro de Distribuição",
              "Tipo de Carga", "Número de Pallets", "Peso Total", "Número de SKUs"],
)

# Save edits back to CSV
if edited_df is not None:
    df = edited_df
    df.to_csv(csv_file_path, index=False)

# Show some metrics and charts about the schedules
st.header("Statistics")

col1, col2, col3 = st.columns(3)
num_scheduled = len(df[df.Status == "Agendado"])
col1.metric(label="Number of scheduled drop-offs", value=num_scheduled, delta=5)
col2.metric(label="Completo drop-offs", value=len(df[df.Status == "Completo"]))
col3.metric(label="Cancelado drop-offs", value=len(df[df.Status == "Cancelado"]))

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
