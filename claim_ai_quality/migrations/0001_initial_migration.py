from django.db import migrations
import os

# Get the database type from environment variable
DB_DEFAULT = os.environ.get('DB_DEFAULT', '').lower()

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
-- Update "tblClaimItems"
UPDATE "tblClaimItems" ci
SET "JsonExt" = jsonb_set(
  "JsonExt"::jsonb,
  '{claim_ai_quality}',
  jsonb_build_object('ai_result', "ClaimItemStatus"::text)
)
WHERE
  "ValidityTo" IS NULL AND
  ("JsonExt"::jsonb -> 'claim_ai_quality' ->> 'ai_result') IS NULL;

-- Update "tblClaimServices"
UPDATE "tblClaimServices" cs
SET "JsonExt" = jsonb_set(
  "JsonExt"::jsonb,
  '{claim_ai_quality}',
  jsonb_build_object('ai_result', "ClaimServiceStatus"::text)
)
WHERE
  "ValidityTo" IS NULL AND
  ("JsonExt"::jsonb -> 'claim_ai_quality' ->> 'ai_result') IS NULL;

-- Update "tblClaim" (with literal constants)
UPDATE "tblClaim" c
SET "JsonExt" = CASE
  WHEN c."ClaimStatus" = 1 AND c."ValidityFromReview" IS NOT NULL THEN
    jsonb_set(c."JsonExt"::jsonb, '{claim_ai_quality}',
      jsonb_build_object(
        'was_categorized', true,
        'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
      ))
  WHEN c."ClaimStatus" = 1 AND c."ValidityFromReview" IS NULL THEN
    jsonb_set(c."JsonExt"::jsonb, '{claim_ai_quality}',
      jsonb_build_object(
        'was_categorized', false,
        'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
      ))
  WHEN c."ClaimStatus" = 4 THEN
    jsonb_set(c."JsonExt"::jsonb, '{claim_ai_quality}',
      jsonb_build_object(
        'was_categorized', false,
        'request_time', 'None',
        'response_time', 'None'
      ))
  WHEN c."ClaimStatus" IN (8, 16) THEN
    jsonb_set(c."JsonExt"::jsonb, '{claim_ai_quality}',
      jsonb_build_object(
        'was_categorized', true,
        'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
      ))
  ELSE c."JsonExt"::jsonb
END
WHERE
  c."ValidityTo" IS NULL AND
  jsonb_typeof(c."JsonExt"::jsonb) IS NOT NULL AND
  (c."JsonExt"::jsonb -> 'claim_ai_quality' ->> 'was_categorized') IS NULL;

-- Create new JsonExt for invalid or null entries

UPDATE "tblClaimItems" ci
SET "JsonExt" = ('{"claim_ai_quality": {"ai_result": "' || "ClaimItemStatus" || '"}}')::jsonb
WHERE
  "ValidityTo" IS NULL AND
  jsonb_typeof("JsonExt"::jsonb) IS NULL;

UPDATE "tblClaimServices" cs
SET "JsonExt" = ('{"claim_ai_quality": {"ai_result": "' || "ClaimServiceStatus" || '"}}')::jsonb
WHERE
  "ValidityTo" IS NULL AND
  jsonb_typeof("JsonExt"::jsonb) IS NULL;

UPDATE "tblClaim" c
SET "JsonExt" = (
  CASE
    WHEN c."ClaimStatus" = 1 AND c."ValidityFromReview" IS NOT NULL THEN
      jsonb_build_object(
        'claim_ai_quality',
        jsonb_build_object(
          'was_categorized', true,
          'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
          'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
        ))
    WHEN c."ClaimStatus" = 1 AND c."ValidityFromReview" IS NULL THEN
      jsonb_build_object(
        'claim_ai_quality',
        jsonb_build_object(
          'was_categorized', false,
          'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
          'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
        ))
    WHEN c."ClaimStatus" = 2 THEN '{}'::jsonb
    WHEN c."ClaimStatus" = 4 THEN
      jsonb_build_object(
        'claim_ai_quality',
        jsonb_build_object(
          'was_categorized', false,
          'request_time', 'None',
          'response_time', 'None'
        ))
    WHEN c."ClaimStatus" IN (8, 16) THEN
      jsonb_build_object(
        'claim_ai_quality',
        jsonb_build_object(
          'was_categorized', true,
          'request_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS'),
          'response_time', to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS')
        ))
    ELSE '{}'::jsonb
  END
)
WHERE
  c."ValidityTo" IS NULL AND
  jsonb_typeof(c."JsonExt"::jsonb) IS NULL;

'''


class Migration(migrations.Migration):
    dependencies = [
        ('claim', '0012_item_service_jsonExtField')
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: run_database_migration(
                schema_editor),
            reverse_code=lambda apps, schema_editor: None
        )
    ]


def run_database_migration(schema_editor):
    # Use environment variable if available, otherwise fallback to database vendor detection
    if DB_DEFAULT == 'postgresql':
        schema_editor.execute(POSTGRESQL_MIGRATION_SQL)
    elif DB_DEFAULT == 'mssql':
        schema_editor.execute(MSSQL_MIGRATION_SQL)
    else:
        # Fallback to database vendor detection if DB_DEFAULT is not set or recognized
        db_engine = schema_editor.connection.vendor

        if db_engine == 'microsoft':  # Microsoft SQL Server
            schema_editor.execute(MSSQL_MIGRATION_SQL)
        elif db_engine == 'postgresql':  # PostgreSQL
            schema_editor.execute(POSTGRESQL_MIGRATION_SQL)
        else:
            # For other database types, you could add more conditions
            # or raise an error for unsupported databases
            raise Exception(
                f"Database engine {db_engine} not supported by this migration")
