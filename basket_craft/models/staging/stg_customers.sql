with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        user_id as customer_id,
        cast(created_at as timestamp) as customer_created_at

    from source
)

select * from renamed
