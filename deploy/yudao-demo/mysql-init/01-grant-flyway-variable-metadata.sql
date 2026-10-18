-- Flyway's MySQL connection cleanup inspects variables owned by the current thread.
-- The app account only needs this table-level grant; it is not granted global PROCESS.
GRANT SELECT ON performance_schema.user_variables_by_thread TO 'otia'@'%';
