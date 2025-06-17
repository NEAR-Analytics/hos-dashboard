SELECT 
    *
FROM external_sources.defillama_protocol_tvl
WHERE TRUE
    AND token IN ('NEAR', 'stNEAR', 'linear-protocol.near', 'LINEAR')