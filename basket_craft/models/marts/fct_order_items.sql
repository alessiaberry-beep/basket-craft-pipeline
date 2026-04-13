{{ config(materialized='table') }}

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

joined as (
    select
        -- primary key
        oi.order_item_id,

        -- foreign keys
        o.customer_id,
        oi.product_id,
        oi.order_id,
        cast(o.order_date as date) as order_date_key,

        -- order header attributes
        o.order_date,

        -- measures
        1 as quantity,
        oi.item_price as unit_price,
        oi.item_price as line_total  -- quantity (1) * unit_price

    from order_items oi
    left join orders o on oi.order_id = o.order_id
)

select * from joined
