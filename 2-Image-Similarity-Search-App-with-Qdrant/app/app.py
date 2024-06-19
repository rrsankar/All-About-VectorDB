from qdrant_client import QdrantClient
import streamlit as st
import base64
from io import BytesIO

# INIT QDRANT COLLECTION NAME
collection_name = "animal_images"


# INIT A STATE VAR.
if "selected_record" not in st.session_state:
    st.session_state.selected_record = None


# FUNC TO SET SELECTED RECORD.
def set_selected_record(new_record):
    st.session_state.selected_record = new_record


# CREATE THE QDRANT CLIENT & CACHE IT.
@st.cache_resource
def get_qdrant_client():
    return QdrantClient(
        url=st.secrets.get("QDRANT_DB_URL"),
        api_key=st.secrets.get("QDRANT_API_KEY")
    )


def get_sample_records():
    """
    FUNC TO GET SOME SAMPLE IMAGES FOR THE USER TO PROVIDE AS INPUT TO FIND SIMILAR IMAGES.
    """

    # INIT QDRANT CLIENT.
    q_client = get_qdrant_client()

    # GET 12 SAMPLE IMAGES TO FIND SIMILARITY.
    # NOTE: DON'T NEED THE VECTOR HERE, JUST THE META DATA.
    sample_records, _ = q_client.scroll(
        collection_name=collection_name,
        with_vectors=False,
        limit=12
    )

    return sample_records


def get_similar_records():
    """
    FUNC TO FIND THE SIMILAR IMAGES IN VECTORDB THAT IS SIMILAR TO INPUT IMAGE.
    """

    # INIT QDRANT CLIENT.
    q_client = get_qdrant_client()

    records_out = []
    if st.session_state.selected_record is not None:
        records_out = q_client.recommend(
            collection_name=collection_name,
            positive=[st.session_state.selected_record.id],
            negative=[],
            limit=12
        )

    return records_out


def convert_base64_to_bytes(base64_input):
    """
    WE HAVE STORED THE IMAGE AS BASE64 IN PAYLOAD AGAINST EACH VECTOR/POINT IN QDRANT.
    THIS FUNC TAKES THE BASE64 INPUT AND CONVERT IT TO BYTES TO RENDER IN THE WEBPAGE.
    """
    return BytesIO(base64.b64decode(base64_input))


# GET THE SAMPLE RECORDS TO SHOW TO USER.
records = get_similar_records() if st.session_state.selected_record is not None else get_sample_records()

# SHOW THE SELECTED RECORD AT TOP.
if st.session_state.selected_record:
    # GET THE BYTES FORMAT OF THE SELECTED IMAGE FROM BASE64 STORED IN PAYLOAD.
    img_bytes = convert_base64_to_bytes(base64_input=st.session_state.selected_record.payload["base64"])
    # SHOW HEADER.
    st.header("Images similar to:")
    # DISPLAY THE IMAGE.
    st.image(image=img_bytes)
    # ADD SPACE IN THE WEBPAGE.
    st.divider()


# SETUP A GRID TO RENDER THE IMAGES.
column = st.columns(3)


for idx, record in enumerate(records):
    # GET IMAGE AS BYTES.
    img_bytes = convert_base64_to_bytes(base64_input=record.payload["base64"])
    # DISPLAY THE IMAGE IN GRID.
    col_idx = idx % 3
    with column[col_idx]:
        st.image(image=img_bytes)
        st.button(
            label="Find similar images",
            key=record.id,
            on_click=set_selected_record,
            args=[record]
        )
