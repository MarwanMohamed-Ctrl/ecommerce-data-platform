
INSERT INTO raw_olist.olist_orders (
    source_file,
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date
)
VALUES
    (
        'ci_fixture.csv', 'ci-order-001', 'ci-customer-001',
        'delivered', '2020-01-01 10:00:00',
        '2020-01-01 11:00:00', '2020-01-01 12:00:00',
        '2020-01-01 13:00:00', '2020-01-05 00:00:00'
    ),
    (
        'ci_fixture.csv', 'ci-order-002', 'ci-customer-002',
        'delivered', '2020-01-01 10:00:00',
        '2020-01-01 09:00:00', '2020-01-01 12:00:00',
        '2020-01-01 13:00:00', '2020-01-05 00:00:00'
    ),
    (
        'ci_fixture.csv', 'ci-order-003', 'ci-customer-003',
        'delivered', '2020-01-01 10:00:00',
        '2020-01-01 11:00:00', '2020-01-01 10:30:00',
        '2020-01-01 13:00:00', '2020-01-05 00:00:00'
    ),
    (
        'ci_fixture.csv', 'ci-order-004', 'ci-customer-004',
        'delivered', '2020-01-01 10:00:00',
        '2020-01-01 11:00:00', '2020-01-01 12:00:00',
        '2020-01-01 10:30:00', '2020-01-05 00:00:00'
    );
