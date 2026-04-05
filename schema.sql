-- Monthly sales summary table for Basket Craft dashboard
CREATE TABLE IF NOT EXISTS monthly_sales_summary (
    year_month      VARCHAR(7)      NOT NULL,
    product_name    VARCHAR(50)     NOT NULL,
    order_count     INTEGER         NOT NULL,
    gross_revenue   NUMERIC(12,2)   NOT NULL,
    refund_amount   NUMERIC(12,2)   NOT NULL,
    net_revenue     NUMERIC(12,2)   NOT NULL,
    avg_order_value NUMERIC(10,2)   NOT NULL,
    PRIMARY KEY (year_month, product_name)
);
