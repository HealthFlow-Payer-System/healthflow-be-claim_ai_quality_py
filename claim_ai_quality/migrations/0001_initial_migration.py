from django.db import migrations

# MSSQL specific SQL
MSSQL_MIGRATION_SQL = '''
-- Add new claim_ai_quality field to already created JsonExt's
declare 
	@CLAIM_STATUS_REJECTED INT = 1,
	@CLAIM_STATUS_ENTERED INT = 2,
	@CLAIM_STATUS_CHECKED INT = 4,
	@CLAIM_STATUS_PROCESSED INT = 8,
	@CLAIM_STATUS_VALUATED INT = 16
	
	
	
update tblClaimItems
    set JsonExt= JSON_MODIFY(
                     CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality', 
                     JSON_QUERY(concat(concat('{"ai_result": "', ClaimItemStatus), '"}'))
                 ) 
    where 
        ValidityTo is null and 
        JSON_VALUE(CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality.ai_result') is Null

    
update tblClaimServices
    set JsonExt= JSON_MODIFY(
                     CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality', 
                     JSON_QUERY(concat(concat('{"ai_result": "', ClaimServiceStatus), '"}'))
                 ) 
    where 
        ValidityTo is null and 
        JSON_VALUE(CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality.ai_result') is Null

update tblClaim
set JsonExt=case 
	when ClaimStatus = @CLAIM_STATUS_REJECTED and ValidityFromReview is not null then 
	    JSON_MODIFY(CONVERT (VARCHAR(MAX), JsonExt) ,'$.claim_ai_quality',  
	         JSON_QUERY(N'{"was_categorized": true,  "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}'))
	
    when ClaimStatus = @CLAIM_STATUS_REJECTED and ValidityFromReview is null then 
	     JSON_MODIFY(CONVERT (VARCHAR(MAX), JsonExt) ,'$.claim_ai_quality', 
	         JSON_QUERY(N'{"was_categorized": false, "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}'))
	
	-- No action on entered status
	
	when ClaimStatus = @CLAIM_STATUS_CHECKED then 
	      JSON_MODIFY(CONVERT (VARCHAR(MAX), JsonExt) ,'$.claim_ai_quality', 
	          JSON_QUERY(N'{"was_categorized": false, "request_time": "None", "response_time": "None"}'))
	
	when ClaimStatus = @CLAIM_STATUS_PROCESSED or ClaimStatus = @CLAIM_STATUS_VALUATED then 
	      JSON_MODIFY(CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality',  
	          JSON_QUERY(N'{"was_categorized": true, "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}'))
	else JsonExt
	end
where ValidityTo is null 
and ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) = 1
and JSON_VALUE(CONVERT (VARCHAR(MAX), JsonExt), '$.claim_ai_quality.was_categorized') is Null


-- Create new JsonExt field
update tblClaimItems
    set  JsonExt=concat(concat('{"claim_ai_quality": {"ai_result": "', ClaimItemStatus), '"}}') 
    where ValidityTo is null and (ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) is null or ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) = 0)

update tblClaimServices
    set JsonExt=concat(concat('{"claim_ai_quality": {"ai_result": "', ClaimServiceStatus), '"}}') 
    where ValidityTo is null and (ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) is null or ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) = 0)
	
	
update tblClaim
set JsonExt=case 
	when ClaimStatus = @CLAIM_STATUS_REJECTED and ValidityFromReview is not null then N'{"claim_ai_quality": {"was_categorized": true, "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}}'
	when ClaimStatus = @CLAIM_STATUS_REJECTED and ValidityFromReview is null then N'{"claim_ai_quality": {"was_categorized": false, "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}}'
	when ClaimStatus = @CLAIM_STATUS_ENTERED then N'{}'
	when ClaimStatus = @CLAIM_STATUS_CHECKED then N'{"claim_ai_quality": {"was_categorized": false, "request_time": "None", "response_time": "None"}}'
	when ClaimStatus = @CLAIM_STATUS_PROCESSED or ClaimStatus = @CLAIM_STATUS_VALUATED then N'{"claim_ai_quality": {"was_categorized": true, "request_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'", "response_time": "'+CONVERT(VARCHAR(30), CURRENT_TIMESTAMP, 121)+N'"}}'
	else N'{}'
	end
where ValidityTo is null and (ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) is null or ISJSON(CONVERT (VARCHAR(MAX), JsonExt)) = 0)
'''

# PostgreSQL compatible SQL
POSTGRESQL_MIGRATION_SQL = '''
DO $$
DECLARE 
	CLAIM_STATUS_REJECTED INT := 1;
	CLAIM_STATUS_ENTERED INT := 2;
	CLAIM_STATUS_CHECKED INT := 4;
	CLAIM_STATUS_PROCESSED INT := 8;
	CLAIM_STATUS_VALUATED INT := 16;
BEGIN

-- Add new claim_ai_quality field to already created JsonExt's for ClaimItems
UPDATE "tblClaimItems"
SET "JsonExt" = (CASE 
    WHEN "JsonExt" IS NULL THEN 
        json_build_object('claim_ai_quality', json_build_object('ai_result', "ClaimItemStatus"))
    WHEN "JsonExt"::jsonb ? 'claim_ai_quality' = false THEN 
        "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object('ai_result', "ClaimItemStatus"))::jsonb
    ELSE "JsonExt"
    END)::json
WHERE "ValidityTo" IS NULL 
AND ("JsonExt" IS NULL OR ("JsonExt"::jsonb -> 'claim_ai_quality' -> 'ai_result') IS NULL);

-- Add new claim_ai_quality field to already created JsonExt's for ClaimServices
UPDATE "tblClaimServices"
SET "JsonExt" = (CASE 
    WHEN "JsonExt" IS NULL THEN 
        json_build_object('claim_ai_quality', json_build_object('ai_result', "ClaimServiceStatus"))
    WHEN "JsonExt"::jsonb ? 'claim_ai_quality' = false THEN 
        "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object('ai_result', "ClaimServiceStatus"))::jsonb
    ELSE "JsonExt"
    END)::json
WHERE "ValidityTo" IS NULL 
AND ("JsonExt" IS NULL OR ("JsonExt"::jsonb -> 'claim_ai_quality' -> 'ai_result') IS NULL);

-- Update tblClaim with proper JSON structure
UPDATE "tblClaim"
SET "JsonExt" = (CASE 
    -- Rejected claims with review
    WHEN "ClaimStatus" = CLAIM_STATUS_REJECTED AND "ValidityFromReview" IS NOT NULL THEN 
        CASE 
            WHEN "JsonExt" IS NULL THEN 
                json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', true,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))
            ELSE 
                "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', true,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))::jsonb
        END
    
    -- Rejected claims without review
    WHEN "ClaimStatus" = CLAIM_STATUS_REJECTED AND "ValidityFromReview" IS NULL THEN 
        CASE 
            WHEN "JsonExt" IS NULL THEN 
                json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', false,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))
            ELSE 
                "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', false,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))::jsonb
        END
    
    -- Checked claims
    WHEN "ClaimStatus" = CLAIM_STATUS_CHECKED THEN 
        CASE 
            WHEN "JsonExt" IS NULL THEN 
                json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', false,
                    'request_time', 'None',
                    'response_time', 'None'
                ))
            ELSE 
                "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', false,
                    'request_time', 'None',
                    'response_time', 'None'
                ))::jsonb
        END
    
    -- Processed or valuated claims
    WHEN "ClaimStatus" = CLAIM_STATUS_PROCESSED OR "ClaimStatus" = CLAIM_STATUS_VALUATED THEN 
        CASE 
            WHEN "JsonExt" IS NULL THEN 
                json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', true,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))
            ELSE 
                "JsonExt"::jsonb || json_build_object('claim_ai_quality', json_build_object(
                    'was_categorized', true,
                    'request_time', CURRENT_TIMESTAMP::text,
                    'response_time', CURRENT_TIMESTAMP::text
                ))::jsonb
        END
    
    -- For ENTERED status, keep as is or initialize with empty JSON
    WHEN "ClaimStatus" = CLAIM_STATUS_ENTERED AND "JsonExt" IS NULL THEN 
        '{}'::json
    
    -- Otherwise leave unchanged
    ELSE "JsonExt"
    END)::json
WHERE "ValidityTo" IS NULL;

END $$;
'''


class Migration(migrations.Migration):
    dependencies = [
        ('claim', '0012_item_service_jsonExtField')
    ]

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # Get database engine being used
        db_engine = schema_editor.connection.vendor

        # Run the appropriate SQL based on database engine
        if db_engine == 'microsoft':  # Microsoft SQL Server
            schema_editor.execute(MSSQL_MIGRATION_SQL)
        elif db_engine == 'postgresql':  # PostgreSQL
            schema_editor.execute(POSTGRESQL_MIGRATION_SQL)
        else:
            # For other database types, you could add more conditions
            # or raise an error for unsupported databases
            raise Exception(
                f"Database engine {db_engine} not supported by this migration")

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # This migration cannot be reversed
        pass

    operations = [
        migrations.RunPython(
            code=database_forwards,
            reverse_code=database_backwards
        )
    ]
