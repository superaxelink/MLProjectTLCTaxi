    """
        Remove rows with missing values in the pickup and dropoff datetime columns in critical columns. 
        This is important because these columns are essential for any analysis related to trip duration, 
        time of day, etc. If these values are missing, it can lead to incorrect calculations and insights.
    """

    """
        **Observation**
        In the NYC Taxi dataset, we found 945748 NaN values simultaneously for in the columns 
        passeenger_count, congestion_surcharge, store_and_fwd_flag, RatecodeID, Airport_fee for 03-2026. 
        
        **Analysis**
        After analyzing the data, we found that all those rows have payment_type = 0. And as per the NYC Taxi dataset documentation, fields describe
            - passenger_count is the number of passengers in the vehicle
            - congestion_surcharge is the total amount collected in trip for NYS congestion surcharge.
            - store_and_fwd_flag This flag indicates whether the trip record was held in vehicle memory before
                sending to the vendor, aka “store and forward,” because the vehicle did not
                have a connection to the server.
                Y = store and forward trip
                N = not a store and forward trip    
            - RatecodeID is the final rate code in effect at the end of the trip.
                1 = Standard rate
                2 = JFK
                3 = Newark
                4 = Nassau or Westchester
                5 = Negotiated fare
                6 = Group ride
                99 = Null/unknown
            - Airport_fee is the fee for pick up only at LaGuardia and John F. Kennedy Airports.
            - payment_type is a numeric code signifying how the passenger paid for the trip, where 
                0 = Flex Fare trip
                1 = Credit card
                2 = Cash
                3 = No charge
                4 = Dispute
                5 = Unknown
                6 = Voided trip

        **Reference:**
        NYC TLC Data Dictionary, yellow_tripdata. 
        https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

        
        From the above, description of the data and noting that all those rows have payment_type = 0, 
        this information may sugges that these rows come from the same type of service. And we can confirm it 
        by checking the unique values of the columns mentioned above.

        **Decision**
        So we choose to exclude those rows from the dataset, due to this analysis focus on metered taxi trips.

        
        **Impact**
        We will lose 945748 rows, which is 23.93% of the total rows.
    """

    """
    Se implementó un motor de reglas genérico en lugar de una lista simple 
    de valores. Aunque hoy solo se usa para una regla (payment_type == 0), 
    se eligió por:
    - Extensibilidad futura (añadir reglas sin tocar lógica)
    - Reutilización en otros pipelines del proyecto
    - Patrón común en ETLs de producción
    """