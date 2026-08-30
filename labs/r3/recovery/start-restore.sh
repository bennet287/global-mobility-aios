#!/bin/sh
set -eu

rm -rf "${PGDATA:?}"/*
cp -a /basebackup/base/. "$PGDATA"/
chmod 700 "$PGDATA"
printf "restore_command = 'cp /wal_archive/%f %p'\n" >> "$PGDATA/postgresql.auto.conf"
printf "recovery_target_time = '%s'\n" "${R3_PITR_TARGET_TIME:?R3_PITR_TARGET_TIME is required}" >> "$PGDATA/postgresql.auto.conf"
printf "recovery_target_action = 'promote'\n" >> "$PGDATA/postgresql.auto.conf"
touch "$PGDATA/recovery.signal"
exec postgres
