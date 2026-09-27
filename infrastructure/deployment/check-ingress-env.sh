#!/bin/sh
set -eu

valid_domain() {
    domain=$1
    case "$domain" in
        ""|*change-this*|*://*|*/*|*:*|*..*|.*|*.|*' '*|*'	'*) return 1 ;;
    esac
    [ "${#domain}" -le 253 ] || return 1
    case "$domain" in *.*) ;; *) return 1 ;; esac

    while :; do
        label=${domain%%.*}
        [ "${#label}" -ge 1 ] && [ "${#label}" -le 63 ] || return 1
        case "$label" in *[!a-z0-9-]*|-*|*-) return 1 ;; esac
        case "$domain" in
            *.*) domain=${domain#*.} ;;
            *) break ;;
        esac
    done

    [ "${#label}" -ge 2 ] || return 1
    case "$label" in example|invalid|localhost|test|*[!a-z]*) return 1 ;; esac
}

if ! valid_domain "${WEB_DOMAIN:-}" || ! valid_domain "${API_DOMAIN:-}" || [ "$WEB_DOMAIN" = "$API_DOMAIN" ]; then
    echo 'Ingress requires distinct public DNS hostnames for WEB_DOMAIN and API_DOMAIN.' >&2
    exit 1
fi

exec "$@"
