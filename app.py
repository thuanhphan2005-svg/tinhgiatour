```python
import streamlit as st
import pymysql
import pandas as pd
from datetime import date, datetime, timedelta


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Hotel Tour Management",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# AIVEN MYSQL CONFIGURATION
# ============================================================

MYSQL_HOST = "mysql-31631392-thuanhphan2005-ad8b.c.aivencloud.com"
MYSQL_PORT = 27590
MYSQL_USER = "avnadmin"
MYSQL_PASSWORD = "AVNS_upB8uNn3pMtP9iw0afh"

# Database mặc định của Aiven MySQL
MYSQL_DATABASE = "defaultdb"


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_connection():
    """
    Tạo kết nối đến MySQL Aiven.

    TLS được bật để mã hóa dữ liệu truyền giữa
    Streamlit và Aiven MySQL.
    """

    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",

        # TLS/SSL
        ssl={
            "check_hostname": False
        },

        connect_timeout=15,
        read_timeout=30,
        write_timeout=30,

        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# ============================================================
# DATABASE HELPER
# ============================================================

def execute_sql(sql, params=None, fetch=False, many=False):
    """
    Chạy SQL và tự commit/rollback.
    """

    conn = None

    try:

        conn = get_connection()

        with conn.cursor() as cursor:

            if many:
                cursor.executemany(sql, params)
            else:
                cursor.execute(sql, params or ())

            if fetch:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid

        conn.commit()

        return result

    except Exception as e:

        if conn:
            conn.rollback()

        raise e

    finally:

        if conn:
            conn.close()


def query_df(sql, params=None):
    """
    Trả kết quả SQL dưới dạng Pandas DataFrame.
    """

    conn = None

    try:

        conn = get_connection()

        df = pd.read_sql_query(
            sql,
            conn,
            params=params
        )

        return df

    finally:

        if conn:
            conn.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    conn = None

    try:

        conn = get_connection()

        with conn.cursor() as cursor:

            # ------------------------------------------------
            # ROOM TYPES
            # ------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_types (
                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(100) NOT NULL UNIQUE,

                    description TEXT,

                    max_adults INT NOT NULL DEFAULT 2,

                    max_children INT NOT NULL DEFAULT 0,

                    base_price DECIMAL(15,2) NOT NULL DEFAULT 0,

                    extra_adult_price DECIMAL(15,2) NOT NULL DEFAULT 0,

                    extra_child_price DECIMAL(15,2) NOT NULL DEFAULT 0,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # ------------------------------------------------
            # ROOMS
            # ------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,

                    room_number VARCHAR(50) NOT NULL UNIQUE,

                    room_type_id INT NOT NULL,

                    floor INT DEFAULT 1,

                    status VARCHAR(30) NOT NULL DEFAULT 'Trống',

                    note TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_rooms_room_type
                    FOREIGN KEY (room_type_id)
                    REFERENCES room_types(id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
                )
                ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # ------------------------------------------------
            # BOOKINGS
            # ------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,

                    booking_code VARCHAR(100) NOT NULL UNIQUE,

                    room_id INT NOT NULL,

                    guest_name VARCHAR(255) NOT NULL,

                    phone VARCHAR(50),

                    tour_code VARCHAR(100),

                    check_in DATE NOT NULL,

                    check_out DATE NOT NULL,

                    adults INT NOT NULL DEFAULT 1,

                    children INT NOT NULL DEFAULT 0,

                    price_per_night DECIMAL(15,2) NOT NULL DEFAULT 0,

                    total_nights INT NOT NULL DEFAULT 0,

                    total_amount DECIMAL(15,2) NOT NULL DEFAULT 0,

                    status VARCHAR(50) NOT NULL DEFAULT 'Đã đặt',

                    note TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_bookings_room
                    FOREIGN KEY (room_id)
                    REFERENCES rooms(id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                    INDEX idx_booking_dates (check_in, check_out),

                    INDEX idx_booking_room (room_id),

                    INDEX idx_booking_status (status)
                )
                ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

        conn.commit()

        # ----------------------------------------------------
        # INSERT SAMPLE ROOM TYPES
        # ----------------------------------------------------

        room_type_count = execute_sql(
            """
            SELECT COUNT(*) AS total
            FROM room_types
            """,
            fetch=True
        )[0]["total"]

        if room_type_count == 0:

            sample_room_types = [
                (
                    "Standard",
                    "Phòng tiêu chuẩn",
                    2,
                    1,
                    800000,
                    200000,
                    100000
                ),
                (
                    "Superior",
                    "Phòng cao cấp",
                    2,
                    2,
                    1100000,
                    250000,
                    120000
                ),
                (
                    "Deluxe",
                    "Phòng Deluxe",
                    2,
                    2,
                    1500000,
                    300000,
                    150000
                ),
                (
                    "Family",
                    "Phòng gia đình",
                    4,
                    2,
                    2000000,
                    300000,
                    150000
                )
            ]

            conn = get_connection()

            try:

                with conn.cursor() as cursor:

                    cursor.executemany(
                        """
                        INSERT INTO room_types
                        (
                            name,
                            description,
                            max_adults,
                            max_children,
                            base_price,
                            extra_adult_price,
                            extra_child_price
                        )
                        VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        sample_room_types
                    )

                conn.commit()

            finally:
                conn.close()

        # ----------------------------------------------------
        # INSERT SAMPLE ROOMS
        # ----------------------------------------------------

        room_count = execute_sql(
            """
            SELECT COUNT(*) AS total
            FROM rooms
            """,
            fetch=True
        )[0]["total"]

        if room_count == 0:

            room_types = query_df(
                """
                SELECT id, name
                FROM room_types
                ORDER BY id
                """
            )

            type_map = {
                row["name"]: int(row["id"])
                for _, row in room_types.iterrows()
            }

            sample_rooms = [
                (
                    "101",
                    type_map["Standard"],
                    1,
                    "Trống",
                    ""
                ),
                (
                    "102",
                    type_map["Standard"],
                    1,
                    "Trống",
                    ""
                ),
                (
                    "103",
                    type_map["Standard"],
                    1,
                    "Trống",
                    ""
                ),
                (
                    "201",
                    type_map["Superior"],
                    2,
                    "Trống",
                    ""
                ),
                (
                    "202",
                    type_map["Superior"],
                    2,
                    "Trống",
                    ""
                ),
                (
                    "203",
                    type_map["Superior"],
                    2,
                    "Bảo trì",
                    "Đang sửa điều hòa"
                ),
                (
                    "301",
                    type_map["Deluxe"],
                    3,
                    "Trống",
                    ""
                ),
                (
                    "302",
                    type_map["Deluxe"],
                    3,
                    "Trống",
                    ""
                ),
                (
                    "401",
                    type_map["Family"],
                    4,
                    "Trống",
                    ""
                ),
                (
                    "402",
                    type_map["Family"],
                    4,
                    "Trống",
                    ""
                )
            ]

            conn = get_connection()

            try:

                with conn.cursor() as cursor:

                    cursor.executemany(
                        """
                        INSERT INTO rooms
                        (
                            room_number,
                            room_type_id,
                            floor,
                            status,
                            note
                        )
                        VALUES
                        (%s, %s, %s, %s, %s)
                        """,
                        sample_rooms
                    )

                conn.commit()

            finally:
                conn.close()


# ============================================================
# CONNECTION TEST + INITIALIZATION
# ============================================================

try:

    init_database()

except Exception as e:

    st.error("❌ Không thể kết nối MySQL Aiven.")

    st.code(
        str(e),
        language="text"
    )

    st.info(
        """
        Kiểm tra:

        1. Aiven MySQL đang hoạt động.
        2. Host và Port chính xác.
        3. Username/password chính xác.
        4. Database đang sử dụng là defaultdb.
        5. Máy tính có Internet.
        6. Đã cài PyMySQL.
        """
    )

    st.stop()


# ============================================================
# HELPER
# ============================================================

def money(value):

    if value is None:
        value = 0

    return f"{float(value):,.0f} đ"


def calculate_nights(check_in, check_out):

    return max(
        (check_out - check_in).days,
        0
    )


def get_room_types():

    return query_df(
        """
        SELECT *
        FROM room_types
        ORDER BY name
        """
    )


def get_rooms():

    return query_df(
        """
        SELECT
            r.id,
            r.room_number,
            r.floor,
            r.status,
            r.note,

            rt.id AS room_type_id,
            rt.name AS room_type,
            rt.base_price,
            rt.max_adults,
            rt.max_children,
            rt.extra_adult_price,
            rt.extra_child_price

        FROM rooms r

        INNER JOIN room_types rt
            ON r.room_type_id = rt.id

        ORDER BY
            r.floor,
            r.room_number
        """
    )


def get_bookings():

    return query_df(
        """
        SELECT
            b.*,

            r.room_number,

            rt.name AS room_type

        FROM bookings b

        INNER JOIN rooms r
            ON b.room_id = r.id

        INNER JOIN room_types rt
            ON r.room_type_id = rt.id

        ORDER BY
            b.check_in DESC,
            b.id DESC
        """
    )


def is_room_available(
    room_id,
    check_in,
    check_out,
    exclude_booking_id=None
):

    sql = """
        SELECT COUNT(*) AS total

        FROM bookings

        WHERE room_id = %s

        AND status NOT IN
        (
            'Đã hủy',
            'Đã trả phòng'
        )

        AND check_in < %s

        AND check_out > %s
    """

    params = [
        room_id,
        check_out,
        check_in
    ]

    if exclude_booking_id:

        sql += """
            AND id != %s
        """

        params.append(
            exclude_booking_id
        )

    result = execute_sql(
        sql,
        params,
        fetch=True
    )

    return result[0]["total"] == 0


def calculate_room_price(
    room_type_id,
    adults,
    children
):

    result = execute_sql(
        """
        SELECT
            base_price,
            max_adults,
            max_children,
            extra_adult_price,
            extra_child_price

        FROM room_types

        WHERE id = %s
        """,
        (room_type_id,),
        fetch=True
    )

    if not result:

        return 0

    room = result[0]

    extra_adults = max(
        adults - int(room["max_adults"]),
        0
    )

    extra_children = max(
        children - int(room["max_children"]),
        0
    )

    price = (
        float(room["base_price"])

        +

        extra_adults
        * float(room["extra_adult_price"])

        +

        extra_children
        * float(room["extra_child_price"])
    )

    return price


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🏨 HOTEL TOUR")

st.sidebar.caption(
    "Hotel Room & Tour Cost Management"
)

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Dashboard",
        "🛏️ Phòng khách sạn",
        "🏷️ Loại phòng",
        "📅 Booking",
        "🧮 Tính giá phòng",
        "📋 Dữ liệu booking"
    ]
)

st.sidebar.divider()

st.sidebar.success(
    "🟢 MySQL Aiven: Connected"
)

st.sidebar.caption(
    f"Database: {MYSQL_DATABASE}"
)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "📊 Dashboard":

    st.title("📊 Dashboard khách sạn")

    rooms = get_rooms()

    bookings = get_bookings()

    total_rooms = len(rooms)

    available_rooms = len(
        rooms[
            rooms["status"] == "Trống"
        ]
    )

    booked_rooms = len(
        rooms[
            rooms["status"] == "Đã đặt"
        ]
    )

    occupied_rooms = len(
        rooms[
            rooms["status"] == "Đang ở"
        ]
    )

    maintenance_rooms = len(
        rooms[
            rooms["status"] == "Bảo trì"
        ]
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Tổng phòng",
        total_rooms
    )

    col2.metric(
        "Phòng trống",
        available_rooms
    )

    col3.metric(
        "Đã đặt",
        booked_rooms
    )

    col4.metric(
        "Đang ở",
        occupied_rooms
    )

    col5.metric(
        "Bảo trì",
        maintenance_rooms
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "📈 Trạng thái phòng"
        )

        if not rooms.empty:

            status_df = (
                rooms["status"]
                .value_counts()
                .rename_axis("Trạng thái")
                .reset_index(
                    name="Số phòng"
                )
            )

            st.bar_chart(
                status_df.set_index(
                    "Trạng thái"
                )
            )

    with col2:

        st.subheader(
            "💰 Doanh thu booking"
        )

        if not bookings.empty:

            revenue = bookings[
                bookings["status"] != "Đã hủy"
            ]["total_amount"].sum()

            st.metric(
                "Tổng giá trị booking",
                money(revenue)
            )

            booking_status = (
                bookings["status"]
                .value_counts()
                .rename_axis("Trạng thái")
                .reset_index(
                    name="Số booking"
                )
            )

            st.dataframe(
                booking_status,
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    st.subheader(
        "🛏️ Danh sách phòng"
    )

    display_rooms = rooms[
        [
            "room_number",
            "room_type",
            "floor",
            "status",
            "base_price",
            "note"
        ]
    ].copy()

    display_rooms.columns = [
        "Phòng",
        "Loại phòng",
        "Tầng",
        "Trạng thái",
        "Giá cơ bản/đêm",
        "Ghi chú"
    ]

    display_rooms[
        "Giá cơ bản/đêm"
    ] = display_rooms[
        "Giá cơ bản/đêm"
    ].apply(money)

    st.dataframe(
        display_rooms,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ROOM MANAGEMENT
# ============================================================

elif menu == "🛏️ Phòng khách sạn":

    st.title(
        "🛏️ Quản lý phòng khách sạn"
    )

    rooms = get_rooms()

    room_types = get_room_types()

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm / sửa phòng"
        ]
    )

    # --------------------------------------------------------
    # ROOM LIST
    # --------------------------------------------------------

    with tab1:

        status_filter = st.multiselect(
            "Lọc trạng thái",
            [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì"
            ],
            default=[
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì"
            ]
        )

        filtered_rooms = rooms[
            rooms["status"].isin(
                status_filter
            )
        ]

        display = filtered_rooms[
            [
                "room_number",
                "room_type",
                "floor",
                "status",
                "base_price",
                "max_adults",
                "max_children",
                "note"
            ]
        ].copy()

        display.columns = [
            "Phòng",
            "Loại phòng",
            "Tầng",
            "Trạng thái",
            "Giá/đêm",
            "NL tối đa",
            "TE tối đa",
            "Ghi chú"
        ]

        display["Giá/đêm"] = display[
            "Giá/đêm"
        ].apply(money)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader(
            "🔄 Cập nhật trạng thái phòng"
        )

        if not rooms.empty:

            room_options = {
                f"Phòng {row.room_number} - "
                f"{row.room_type}":
                row.id

                for row in rooms.itertuples()
            }

            selected_room = st.selectbox(
                "Chọn phòng",
                list(
                    room_options.keys()
                )
            )

            selected_room_id = room_options[
                selected_room
            ]

            current_room = rooms[
                rooms["id"] ==
                selected_room_id
            ].iloc[0]

            new_status = st.selectbox(
                "Trạng thái",
                [
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Bảo trì"
                ],
                index=[
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Bảo trì"
                ].index(
                    current_room["status"]
                )
            )

            if st.button(
                "💾 Cập nhật",
                type="primary"
            ):

                execute_sql(
                    """
                    UPDATE rooms

                    SET status = %s

                    WHERE id = %s
                    """,
                    (
                        new_status,
                        selected_room_id
                    )
                )

                st.success(
                    "Đã cập nhật trạng thái."
                )

                st.rerun()

    # --------------------------------------------------------
    # ADD / EDIT ROOM
    # --------------------------------------------------------

    with tab2:

        mode = st.radio(
            "Thao tác",
            [
                "Thêm phòng",
                "Sửa phòng"
            ],
            horizontal=True
        )

        if mode == "Thêm phòng":

            with st.form(
                "add_room_form"
            ):

                room_number = st.text_input(
                    "Số phòng *",
                    placeholder="Ví dụ: 105"
                )

                room_type_map = {
                    row["name"]:
                    int(row["id"])

                    for _, row
                    in room_types.iterrows()
                }

                room_type_name = st.selectbox(
                    "Loại phòng",
                    list(
                        room_type_map.keys()
                    )
                )

                floor = st.number_input(
                    "Tầng",
                    min_value=1,
                    max_value=100,
                    value=1
                )

                status = st.selectbox(
                    "Trạng thái",
                    [
                        "Trống",
                        "Đã đặt",
                        "Đang ở",
                        "Bảo trì"
                    ]
                )

                note = st.text_area(
                    "Ghi chú"
                )

                submitted = st.form_submit_button(
                    "➕ Thêm phòng",
                    type="primary"
                )

                if submitted:

                    if not room_number.strip():

                        st.error(
                            "Vui lòng nhập số phòng."
                        )

                    else:

                        try:

                            execute_sql(
                                """
                                INSERT INTO rooms
                                (
                                    room_number,
                                    room_type_id,
                                    floor,
                                    status,
                                    note
                                )

                                VALUES
                                (
                                    %s,
                                    %s,
                                    %s,
                                    %s,
                                    %s
                                )
                                """,
                                (
                                    room_number.strip(),
                                    room_type_map[
                                        room_type_name
                                    ],
                                    floor,
                                    status,
                                    note
                                )
                            )

                            st.success(
                                f"Đã thêm phòng "
                                f"{room_number}."
                            )

                            st.rerun()

                        except pymysql.err.IntegrityError:

                            st.error(
                                "Số phòng đã tồn tại."
                            )

        else:

            if rooms.empty:

                st.info(
                    "Chưa có phòng."
                )

            else:

                room_map = {
                    f"{row.room_number} - "
                    f"{row.room_type}":
                    row.id

                    for row in rooms.itertuples()
                }

                selected = st.selectbox(
                    "Chọn phòng",
                    list(room_map.keys())
                )

                room_id = room_map[selected]

                room = rooms[
                    rooms["id"] == room_id
                ].iloc[0]

                with st.form(
                    "edit_room_form"
                ):

                    room_number = st.text_input(
                        "Số phòng",
                        value=room[
                            "room_number"
                        ]
                    )

                    room_type_names = list(
                        room_types["name"]
                    )

                    current_type_index = (
                        room_type_names.index(
                            room["room_type"]
                        )
                    )

                    room_type_name = st.selectbox(
                        "Loại phòng",
                        room_type_names,
                        index=current_type_index
                    )

                    floor = st.number_input(
                        "Tầng",
                        min_value=1,
                        max_value=100,
                        value=int(
                            room["floor"]
                        )
                    )

                    status = st.selectbox(
                        "Trạng thái",
                        [
                            "Trống",
                            "Đã đặt",
                            "Đang ở",
                            "Bảo trì"
                        ],
                        index=[
                            "Trống",
                            "Đã đặt",
                            "Đang ở",
                            "Bảo trì"
                        ].index(
                            room["status"]
                        )
                    )

                    note = st.text_area(
                        "Ghi chú",
                        value=room["note"] or ""
                    )

                    submitted = st.form_submit_button(
                        "💾 Lưu thay đổi",
                        type="primary"
                    )

                    if submitted:

                        type_id = int(
                            room_types[
                                room_types["name"]
                                == room_type_name
                            ].iloc[0]["id"]
                        )

                        try:

                            execute_sql(
                                """
                                UPDATE rooms

                                SET
                                    room_number = %s,
                                    room_type_id = %s,
                                    floor = %s,
                                    status = %s,
                                    note = %s

                                WHERE id = %s
                                """,
                                (
                                    room_number,
                                    type_id,
                                    floor,
                                    status,
                                    note,
                                    room_id
                                )
                            )

                            st.success(
                                "Đã cập nhật phòng."
                            )

                            st.rerun()

                        except pymysql.err.IntegrityError:

                            st.error(
                                "Số phòng đã tồn tại."
                            )


# ============================================================
# ROOM TYPE MANAGEMENT
# ============================================================

elif menu == "🏷️ Loại phòng":

    st.title(
        "🏷️ Quản lý loại phòng"
    )

    room_types = get_room_types()

    display = room_types[
        [
            "name",
            "description",
            "max_adults",
            "max_children",
            "base_price",
            "extra_adult_price",
            "extra_child_price"
        ]
    ].copy()

    display.columns = [
        "Loại phòng",
        "Mô tả",
        "NL tối đa",
        "TE tối đa",
        "Giá cơ bản",
        "Phụ thu NL",
        "Phụ thu TE"
    ]

    for col in [
        "Giá cơ bản",
        "Phụ thu NL",
        "Phụ thu TE"
    ]:

        display[col] = display[
            col
        ].apply(money)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    tab1, tab2 = st.tabs(
        [
            "➕ Thêm loại phòng",
            "✏️ Sửa loại phòng"
        ]
    )

    # --------------------------------------------------------
    # ADD ROOM TYPE
    # --------------------------------------------------------

    with tab1:

        with st.form(
            "add_room_type"
        ):

            name = st.text_input(
                "Tên loại phòng *",
                placeholder="Ví dụ: Suite"
            )

            description = st.text_area(
                "Mô tả"
            )

            col1, col2 = st.columns(2)

            with col1:

                max_adults = st.number_input(
                    "Người lớn tiêu chuẩn",
                    min_value=1,
                    value=2
                )

                base_price = st.number_input(
                    "Giá cơ bản / đêm",
                    min_value=0,
                    value=1000000,
                    step=50000
                )

                extra_adult_price = st.number_input(
                    "Phụ thu người lớn",
                    min_value=0,
                    value=200000,
                    step=50000
                )

            with col2:

                max_children = st.number_input(
                    "Trẻ em tiêu chuẩn",
                    min_value=0,
                    value=1
                )

                extra_child_price = st.number_input(
                    "Phụ thu trẻ em",
                    min_value=0,
                    value=100000,
                    step=50000
                )

            submitted = st.form_submit_button(
                "➕ Thêm loại phòng",
                type="primary"
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Vui lòng nhập tên."
                    )

                else:

                    try:

                        execute_sql(
                            """
                            INSERT INTO room_types
                            (
                                name,
                                description,
                                max_adults,
                                max_children,
                                base_price,
                                extra_adult_price,
                                extra_child_price
                            )

                            VALUES
                            (
                                %s, %s, %s, %s,
                                %s, %s, %s
                            )
                            """,
                            (
                                name.strip(),
                                description,
                                max_adults,
                                max_children,
                                base_price,
                                extra_adult_price,
                                extra_child_price
                            )
                        )

                        st.success(
                            "Đã thêm loại phòng."
                        )

                        st.rerun()

                    except pymysql.err.IntegrityError:

                        st.error(
                            "Tên loại phòng đã tồn tại."
                        )

    # --------------------------------------------------------
    # EDIT ROOM TYPE
    # --------------------------------------------------------

    with tab2:

        if room_types.empty:

            st.info(
                "Chưa có loại phòng."
            )

        else:

            type_map = {
                row["name"]:
                int(row["id"])

                for _, row
                in room_types.iterrows()
            }

            selected_name = st.selectbox(
                "Chọn loại phòng",
                list(type_map.keys())
            )

            selected_type = room_types[
                room_types["name"]
                == selected_name
            ].iloc[0]

            with st.form(
                "edit_room_type"
            ):

                name = st.text_input(
                    "Tên loại phòng",
                    value=selected_type["name"]
                )

                description = st.text_area(
                    "Mô tả",
                    value=(
                        selected_type[
                            "description"
                        ] or ""
                    )
                )

                col1, col2 = st.columns(2)

                with col1:

                    max_adults = st.number_input(
                        "Người lớn tiêu chuẩn",
                        min_value=1,
                        value=int(
                            selected_type[
                                "max_adults"
                            ]
                        )
                    )

                    base_price = st.number_input(
                        "Giá cơ bản / đêm",
                        min_value=0,
                        value=int(
                            float(
                                selected_type[
                                    "base_price"
                                ]
                            )
                        ),
                        step=50000
                    )

                    extra_adult_price = st.number_input(
                        "Phụ thu người lớn",
                        min_value=0,
                        value=int(
                            float(
                                selected_type[
                                    "extra_adult_price"
                                ]
                            )
                        ),
                        step=50000
                    )

                with col2:

                    max_children = st.number_input(
                        "Trẻ em tiêu chuẩn",
                        min_value=0,
                        value=int(
                            selected_type[
                                "max_children"
                            ]
                        )
                    )

                    extra_child_price = st.number_input(
                        "Phụ thu trẻ em",
                        min_value=0,
                        value=int(
                            float(
                                selected_type[
                                    "extra_child_price"
                                ]
                            )
                        ),
                        step=50000
                    )

                submitted = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    type="primary"
                )

                if submitted:

                    try:

                        execute_sql(
                            """
                            UPDATE room_types

                            SET
                                name = %s,
                                description = %s,
                                max_adults = %s,
                                max_children = %s,
                                base_price = %s,
                                extra_adult_price = %s,
                                extra_child_price = %s

                            WHERE id = %s
                            """,
                            (
                                name.strip(),
                                description,
                                max_adults,
                                max_children,
                                base_price,
                                extra_adult_price,
                                extra_child_price,
                                selected_type["id"]
                            )
                        )

                        st.success(
                            "Đã cập nhật."
                        )

                        st.rerun()

                    except pymysql.err.IntegrityError:

                        st.error(
                            "Tên loại phòng đã tồn tại."
                        )


# ============================================================
# BOOKING
# ============================================================

elif menu == "📅 Booking":

    st.title(
        "📅 Quản lý Booking"
    )

    rooms = get_rooms()

    if rooms.empty:

        st.warning(
            "Chưa có phòng."
        )

        st.stop()

    st.subheader(
        "➕ Tạo booking"
    )

    with st.form(
        "booking_form"
    ):

        col1, col2, col3 = st.columns(3)

        with col1:

            booking_code = st.text_input(
                "Mã booking *",
                value=(
                    "BK"
                    +
                    datetime.now().strftime(
                        "%Y%m%d%H%M%S"
                    )
                )
            )

            guest_name = st.text_input(
                "Tên khách *"
            )

            phone = st.text_input(
                "Số điện thoại"
            )

            tour_code = st.text_input(
                "Mã tour"
            )

        with col2:

            check_in = st.date_input(
                "Ngày check-in",
                value=date.today()
            )

            check_out = st.date_input(
                "Ngày check-out",
                value=(
                    date.today()
                    + timedelta(days=1)
                )
            )

            adults = st.number_input(
                "Người lớn",
                min_value=1,
                value=2
            )

            children = st.number_input(
                "Trẻ em",
                min_value=0,
                value=0
            )

        with col3:

            available_rooms = rooms[
                rooms["status"] != "Bảo trì"
            ]

            room_options = {
                f"Phòng {row.room_number} - "
                f"{row.room_type} - "
                f"{money(row.base_price)}/đêm":
                int(row.id)

                for row
                in available_rooms.itertuples()
            }

            if not room_options:

                st.error(
                    "Không có phòng."
                )

                st.stop()

            selected_room = st.selectbox(
                "Chọn phòng",
                list(room_options.keys())
            )

            room_id = room_options[
                selected_room
            ]

            selected_room_data = rooms[
                rooms["id"] == room_id
            ].iloc[0]

            calculated_price = (
                calculate_room_price(
                    selected_room_data[
                        "room_type_id"
                    ],
                    adults,
                    children
                )
            )

            nights_preview = calculate_nights(
                check_in,
                check_out
            )

            st.metric(
                "Giá phòng / đêm",
                money(calculated_price)
            )

            st.metric(
                "Số đêm",
                nights_preview
            )

            st.metric(
                "Tạm tính",
                money(
                    calculated_price
                    * nights_preview
                )
            )

        note = st.text_area(
            "Ghi chú"
        )

        submitted = st.form_submit_button(
            "💾 Tạo booking",
            type="primary"
        )

        if submitted:

            if not booking_code.strip():

                st.error(
                    "Vui lòng nhập mã booking."
                )

            elif not guest_name.strip():

                st.error(
                    "Vui lòng nhập tên khách."
                )

            elif check_out <= check_in:

                st.error(
                    "Check-out phải sau check-in."
                )

            elif not is_room_available(
                room_id,
                check_in,
                check_out
            ):

                st.error(
                    "Phòng đã có booking "
                    "trùng thời gian."
                )

            else:

                nights = calculate_nights(
                    check_in,
                    check_out
                )

                total = (
                    calculated_price
                    * nights
                )

                try:

                    execute_sql(
                        """
                        INSERT INTO bookings
                        (
                            booking_code,
                            room_id,
                            guest_name,
                            phone,
                            tour_code,
                            check_in,
                            check_out,
                            adults,
                            children,
                            price_per_night,
                            total_nights,
                            total_amount,
                            status,
                            note
                        )

                        VALUES
                        (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s
                        )
                        """,
                        (
                            booking_code.strip(),
                            room_id,
                            guest_name.strip(),
                            phone,
                            tour_code,
                            check_in,
                            check_out,
                            adults,
                            children,
                            calculated_price,
                            nights,
                            total,
                            "Đã đặt",
                            note
                        )
                    )

                    execute_sql(
                        """
                        UPDATE rooms

                        SET status = 'Đã đặt'

                        WHERE id = %s

                        AND status = 'Trống'
                        """,
                        (room_id,)
                    )

                    st.success(
                        f"Đã tạo booking "
                        f"{booking_code}. "
                        f"Tổng: {money(total)}"
                    )

                    st.rerun()

                except pymysql.err.IntegrityError:

                    st.error(
                        "Mã booking đã tồn tại."
                    )


# ============================================================
# PRICE CALCULATOR
# ============================================================

elif menu == "🧮 Tính giá phòng":

    st.title(
        "🧮 Tính giá phòng"
    )

    room_types = get_room_types()

    if room_types.empty:

        st.warning(
            "Chưa có loại phòng."
        )

        st.stop()

    type_map = {
        row["name"]:
        int(row["id"])

        for _, row
        in room_types.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:

        room_type_name = st.selectbox(
            "Loại phòng",
            list(type_map.keys())
        )

        room_type_id = type_map[
            room_type_name
        ]

        adults = st.number_input(
            "Số người lớn",
            min_value=1,
            value=2
        )

        children = st.number_input(
            "Số trẻ em",
            min_value=0,
            value=0
        )

        nights = st.number_input(
            "Số đêm",
            min_value=1,
            value=2
        )

    with col2:

        room_type = room_types[
            room_types["id"]
            == room_type_id
        ].iloc[0]

        st.info(
            f"""
**{room_type_name}**

Người lớn tiêu chuẩn:
{room_type["max_adults"]}

Trẻ em tiêu chuẩn:
{room_type["max_children"]}

Giá cơ bản:
{money(room_type["base_price"])}
"""
        )

        price_per_night = (
            calculate_room_price(
                room_type_id,
                adults,
                children
            )
        )

        total_price = (
            price_per_night
            * nights
        )

        st.metric(
            "Giá / phòng / đêm",
            money(price_per_night)
        )

        st.metric(
            "Tổng tiền",
            money(total_price)
        )

    st.divider()

    st.subheader(
        "📋 Chi tiết tính giá"
    )

    extra_adults = max(
        adults
        - int(room_type["max_adults"]),
        0
    )

    extra_children = max(
        children
        - int(room_type["max_children"]),
        0
    )

    base_total = (
        float(room_type["base_price"])
        * nights
    )

    adult_surcharge = (
        extra_adults
        * float(
            room_type[
                "extra_adult_price"
            ]
        )
        * nights
    )

    child_surcharge = (
        extra_children
        * float(
            room_type[
                "extra_child_price"
            ]
        )
        * nights
    )

    price_detail = pd.DataFrame(
        {
            "Khoản mục": [
                "Giá phòng cơ bản",
                "Phụ thu người lớn",
                "Phụ thu trẻ em",
                "TỔNG"
            ],

            "Thành tiền": [
                base_total,
                adult_surcharge,
                child_surcharge,
                total_price
            ]
        }
    )

    price_detail[
        "Thành tiền"
    ] = price_detail[
        "Thành tiền"
    ].apply(money)

    st.dataframe(
        price_detail,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BOOKING DATA
# ============================================================

elif menu == "📋 Dữ liệu booking":

    st.title(
        "📋 Dữ liệu booking"
    )

    bookings = get_bookings()

    if bookings.empty:

        st.info(
            "Chưa có booking."
        )

        st.stop()

    col1, col2 = st.columns(2)

    with col1:

        status_filter = st.multiselect(
            "Trạng thái",
            sorted(
                bookings[
                    "status"
                ].unique()
            ),
            default=sorted(
                bookings[
                    "status"
                ].unique()
            )
        )

    with col2:

        search = st.text_input(
            "🔎 Tìm booking / khách / tour"
        )

    filtered = bookings[
        bookings["status"].isin(
            status_filter
        )
    ].copy()

    if search.strip():

        search_lower = (
            search.strip().lower()
        )

        filtered = filtered[
            filtered.apply(
                lambda row:

                search_lower
                in str(
                    row["booking_code"]
                ).lower()

                or

                search_lower
                in str(
                    row["guest_name"]
                ).lower()

                or

                search_lower
                in str(
                    row["tour_code"]
                ).lower(),

                axis=1
            )
        ]

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Số booking",
            len(filtered)
        )

    with col2:

        st.metric(
            "Tổng giá trị",
            money(
                filtered[
                    "total_amount"
                ].sum()
            )
        )

    display = filtered[
        [
            "booking_code",
            "guest_name",
            "phone",
            "tour_code",
            "room_number",
            "room_type",
            "check_in",
            "check_out",
            "adults",
            "children",
            "total_nights",
            "price_per_night",
            "total_amount",
            "status",
            "note"
        ]
    ].copy()

    display.columns = [
        "Booking",
        "Khách",
        "Điện thoại",
        "Mã tour",
        "Phòng",
        "Loại phòng",
        "Check-in",
        "Check-out",
        "NL",
        "TE",
        "Đêm",
        "Giá/đêm",
        "Tổng tiền",
        "Trạng thái",
        "Ghi chú"
    ]

    display[
        "Giá/đêm"
    ] = display[
        "Giá/đêm"
    ].apply(money)

    display[
        "Tổng tiền"
    ] = display[
        "Tổng tiền"
    ].apply(money)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader(
        "⚙️ Thao tác booking"
    )

    booking_options = {
        f"{row.booking_code} - "
        f"{row.guest_name} - "
        f"Phòng {row.room_number}":
        int(row.id)

        for row
        in filtered.itertuples()
    }

    if booking_options:

        selected_booking_label = st.selectbox(
            "Chọn booking",
            list(
                booking_options.keys()
            )
        )

        booking_id = booking_options[
            selected_booking_label
        ]

        booking = bookings[
            bookings["id"]
            == booking_id
        ].iloc[0]

        col1, col2, col3 = st.columns(3)

        # ----------------------------------------------------
        # CHECK IN
        # ----------------------------------------------------

        with col1:

            if st.button(
                "🟢 Check-in",
                use_container_width=True
            ):

                execute_sql(
                    """
                    UPDATE bookings

                    SET status = 'Đang ở'

                    WHERE id = %s
                    """,
                    (booking_id,)
                )

                execute_sql(
                    """
                    UPDATE rooms

                    SET status = 'Đang ở'

                    WHERE id = %s
                    """,
                    (booking["room_id"],)
                )

                st.success(
                    "Đã check-in."
                )

                st.rerun()

        # ----------------------------------------------------
        # CHECK OUT
        # ----------------------------------------------------

        with col2:

            if st.button(
                "🔵 Check-out",
                use_container_width=True
            ):

                execute_sql(
                    """
                    UPDATE bookings

                    SET status = 'Đã trả phòng'

                    WHERE id = %s
                    """,
                    (booking_id,)
                )

                execute_sql(
                    """
                    UPDATE rooms

                    SET status = 'Trống'

                    WHERE id = %s
                    """,
                    (booking["room_id"],)
                )

                st.success(
                    "Đã check-out."
                )

                st.rerun()

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        with col3:

            if st.button(
                "🔴 Hủy booking",
                use_container_width=True
            ):

                execute_sql(
                    """
                    UPDATE bookings

                    SET status = 'Đã hủy'

                    WHERE id = %s
                    """,
                    (booking_id,)
                )

                execute_sql(
                    """
                    UPDATE rooms

                    SET status = 'Trống'

                    WHERE id = %s

                    AND status = 'Đã đặt'
                    """,
                    (booking["room_id"],)
                )

                st.success(
                    "Đã hủy booking."
                )

                st.rerun()

    st.divider()

    csv = filtered.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        "⬇️ Xuất booking CSV",
        data=csv,
        file_name="bookings.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "🏨 Hotel Tour Management"
)

st.sidebar.caption(
    "Streamlit + MySQL + Aiven"
)
```
