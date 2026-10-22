CREATE OR REPLACE VIEW staging.stg_orders AS
SELECT
    source_row_number,
    source_file,
    ingested_at,
    NULLIF(order_id, '') AS order_id,
    NULLIF(customer_id, '') AS customer_id,
    NULLIF(order_status, '') AS order_status,
    NULLIF(order_purchase_timestamp, '')::timestamp
        AS order_purchase_timestamp,
    NULLIF(order_approved_at, '')::timestamp
        AS order_approved_at,
    NULLIF(order_delivered_carrier_date, '')::timestamp
        AS order_delivered_carrier_date,
    NULLIF(order_delivered_customer_date, '')::timestamp
        AS order_delivered_customer_date,
    NULLIF(order_estimated_delivery_date, '')::timestamp
        AS order_estimated_delivery_date,
    (
        NULLIF(order_approved_at, '')::timestamp
        < NULLIF(order_purchase_timestamp, '')::timestamp
    ) AS is_approval_before_purchase,
    (
        NULLIF(order_delivered_carrier_date, '')::timestamp
        < NULLIF(order_approved_at, '')::timestamp
    ) AS is_carrier_before_approval,
    (
        NULLIF(order_delivered_customer_date, '')::timestamp
        < NULLIF(order_delivered_carrier_date, '')::timestamp
    ) AS is_customer_delivery_before_carrier
FROM raw_olist.olist_orders;
