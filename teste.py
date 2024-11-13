import datetime
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import time
from sqlalchemy.orm import sessionmaker

def get_finishing_time(start_date, start_time, category):
    offloading_duration = {
        "Pallet Monoproduto": datetime.timedelta(minutes=30),
        "Pallet Misto": datetime.timedelta(minutes=60),
        "Estivado": datetime.timedelta(minutes=120)
    }
    start_datetime = datetime.datetime.combine(start_date, start_time)
    duration = offloading_duration.get(category, datetime.timedelta())
    end_time = start_datetime + duration
    return end_time.time()

# SQLAlchemy connection setup
db_config = st.secrets["mysql"]
engine = create_engine(
    f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)

# Set up a session
Session = sessionmaker(bind=engine)
session = Session()

def insert_schedule(schedule_data):
    try:
        insert_query = text("""
            INSERT INTO Schedules 
            (ID, Supplier_Name, Invoice_Number, Dropoff_Date, Dropoff_Time, Status, Distribution_Center, Load_Type, 
            Pallet_Number, Total_Weight, SKU_Count, Created_At) 
            VALUES (:ID, :Supplier_Name, :Invoice_Number, :Dropoff_Date, :Dropoff_Time, :Status, 
                    :Distribution_Center, :Load_Type, :Pallet_Number, :Total_Weight, :SKU_Count, :Created_At);
        """)
        session.execute(insert_query, schedule_data)
        session.commit()  # Commit the transaction
        st.success("Agendamento enviado! Aqui estão os detalhes:")
        st.dataframe(pd.DataFrame([schedule_data]), use_container_width=True, hide_index=True)
    except SQLAlchemyError as e:
        session.rollback()  # Rollback in case of error
        st.error(f"Erro ao inserir o agendamento: {str(e)}")
    finally:
        session.close()

def load_schedules():
    with engine.connect() as conn:
        query = "SELECT * FROM Schedules"
        dataframe = pd.read_sql(query, conn)
    return dataframe

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

df = load_schedules()

# Section to add a new schedule
st.header("Adicionar Agendamento")

with st.form("add_schedule_form"):
    supplier_name = st.text_input("Indústria")
    invoice = st.text_input("Número da NF")
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
max_schedules = {'CLAS': 10, 'JSL': 6, 'GPA': 7}

# Define the maximum number of simultaneous schedules
max_simulatenous = 2

# Minimum Time
minimum_time = {'CLAS': time(7, 0), 'JSL': time(13, 00), 'GPA': time(7, 0)}

# Maximum Time
maximum_time = {'CLAS': time(15, 0), 'JSL': time(20, 00), 'GPA': time(14, 0)}

if submitted:
    # Check how many schedules are already set for the selected drop-off date
    schedules_on_date = df[(df["Dropoff_Date"] == str(dropoff_date)) &
                           (df["Distribution_Center"] == distribution_center)]
    if len(schedules_on_date) >= max_schedules[distribution_center]:
        st.error(
            f"Não é possível agendar mais de {max_schedules[distribution_center]} entregas para o dia {dropoff_date} por Centro de Distribuição.")
    elif dropoff_time < minimum_time[distribution_center] or dropoff_time > maximum_time[distribution_center]:
        st.error(
            f"É necessário agendar entre às {minimum_time[distribution_center]} e {maximum_time[distribution_center]}")
    else:
        if df.empty or df.ID.isnull().all():
            recent_schedule_id = 0
        else:
            recent_schedule_id = int(max(df.ID).split("-")[1])
        new_schedule = {
            "ID": f"SCHEDULE-{recent_schedule_id + 1}",
            "Supplier_Name": supplier_name,
            "Invoice_Number": invoice,
            "Dropoff_Date": dropoff_date,
            "Dropoff_Time": dropoff_time.strftime("%H:%M"),
            "Status": status,
            "Distribution_Center": distribution_center,
            "Load_Type": load_type,
            "Pallet_Number": pallet_number,
            "Total_Weight": total_weight,
            "SKU_Count": sku_number,
            "Created_At": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        insert_schedule(new_schedule)
