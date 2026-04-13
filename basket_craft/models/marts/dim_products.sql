{{ config(materialized='table') }}

with products as (
    select * from {{ ref('stg_products') }}
)

select
    product_id,
    product_name,
    product_price

from products
