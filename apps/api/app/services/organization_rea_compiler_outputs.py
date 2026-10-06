"""Fixed compiler-workflow identities authenticate manifests, not arbitrary jobs.

No lane claim in a caller-controlled predicate grants identity. The two distinct
reviewed reusable workflow paths are authenticated by their certificates.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from app.services import organization_rea_ci_attestation as ci
from app.services.organization_command import canonical_json
from app.services.organization_rea_source_relation import COMPILER_PATHS

@dataclass(frozen=True)
class ReaCompilerLaneTrust:
    manifest_root: Path
    manifest_relative: str
    bundle_root: Path
    bundle_relative: str
    manifest_sha256: str
    bundle_sha256: str
    workflow_sha256: str

@dataclass(frozen=True)
class ReaCompilerOutputsTrust:
    a: ReaCompilerLaneTrust
    b: ReaCompilerLaneTrust


def reviewed_pins(trust, approved):
    ci.require(type(trust) is ReaCompilerOutputsTrust and approved is not None, 'compiler output review/trust missing')
    result = {}
    for lane in ('a', 'b'):
        value = getattr(trust, lane)
        ci.require(type(value) is ReaCompilerLaneTrust, 'fixed compiler lane trust missing')
        pins = {key:getattr(value,key) for key in ('manifest_sha256','bundle_sha256','workflow_sha256')}
        ci.require(all(type(v) is str and re.fullmatch(r'[0-9a-f]{64}',v) is not None for v in pins.values()), 'compiler lane digest invalid')
        ci.require(pins == getattr(approved,lane).model_dump(mode='json'), 'compiler deployment pins differ from Board review')
        result[lane] = value.workflow_sha256
    ci.require(trust.a.bundle_sha256 != trust.b.bundle_sha256 and trust.a.manifest_sha256 != trust.b.manifest_sha256, 'compiler lanes cannot reuse evidence')
    return result


def locators(trust):
    return [locator for lane in ('a','b') for locator in (
        (getattr(trust,lane).manifest_root,getattr(trust,lane).manifest_relative,ci.MAX_JSON),
        (getattr(trust,lane).bundle_root,getattr(trust,lane).bundle_relative,ci.MAX_JSON))]


def _identity(expected, lane):
    result = dict(expected)
    signer = f'https://github.com/{ci.REPOSITORY}/{COMPILER_PATHS[("a", "b").index(lane)]}@{expected["sourceRepositoryRef"]}'
    result.update(subjectAlternativeName=signer,buildSignerURI=signer)
    # Same-repository local reusable workflow references resolve at the exact
    # caller revision. buildConfig remains the caller; signer is the callee.
    return result


def authenticate(report_raw, archive, expected, trust, snapshots):
    ci.require(len(snapshots)==4, 'compiler raw snapshots missing')
    report=ci.parse_json(report_raw)
    ci.require(type(report) is dict and report.get('format')=='aios-rea-package-correlation.v1', 'compiler correlation report missing')
    repeated=report.get('repeatability')
    ci.require(type(repeated) is dict and repeated.get('context') == expected['context'], 'compiler report context differs')
    received=repeated.get('received_manifest_sha256')
    ci.require(type(received) is dict and set(received)=={'a','b'}, 'compiler correlation hashes missing')
    summary={}
    for index,lane in enumerate(('a','b')):
        manifest_raw,bundle=snapshots[index*2][0],snapshots[index*2+1][0]
        pins=getattr(trust,lane)
        ci.require(ci.sha(manifest_raw)==pins.manifest_sha256==received[lane] and ci.sha(bundle)==pins.bundle_sha256, 'compiler raw evidence digest differs')
        proof=ci._verify_raw_subject(manifest_raw,bundle,archive,_identity(expected,lane),_subject_name='manifest.json')
        value=ci.parse_json(manifest_raw)
        ci.require(type(value) is dict and set(value)=={'format','context','job','captured_at','source','toolchain','recipe','files'} and value['format']=='aios-rea-build-job.v1', 'compiler manifest schema differs')
        ci.require(value['job']==lane and canonical_json(value['context'])==canonical_json(expected['context']), 'compiler manifest lane/context differs')
        for key in ('source','toolchain','recipe','files'):
            ci.require(canonical_json(value[key])==canonical_json(repeated.get(key)), 'compiler manifest/report inputs or complete files differ')
        stamp=value['captured_at']
        ci.require(type(stamp) is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?\+00:00',stamp) is not None,'compiler capture time invalid')
        try:
            parsed=datetime.fromisoformat(stamp)
        except ValueError as exc:
            raise ci.EvidenceError('compiler capture time invalid') from exc
        ci.require(parsed<=datetime.now(timezone.utc),'compiler capture time future')
        certificate=_identity(expected,lane)
        summary[lane]={'manifest_sha256':ci.sha(manifest_raw),'bundle_sha256':ci.sha(bundle),
            'workflow_sha256':pins.workflow_sha256,
            'certificate':{key:proof['certificate'][key] for key in certificate if key!='context'},
            'verified_timestamps':[{key:item[key] for key in ('type','timestamp')} for item in proof['verified_timestamps']],
            'fresh_cli_output_sha256':proof['fresh_cli_output_sha256']}
    return summary
