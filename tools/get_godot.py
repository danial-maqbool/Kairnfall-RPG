"""Fetch the pinned official Godot .NET release and verify published digests."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import urllib.request
import zipfile

VERSION='4.7.2'
API=f'https://api.github.com/repos/godotengine/godot/releases/tags/{VERSION}-stable'

def request(url):
    return urllib.request.Request(url,headers={'User-Agent':'Kairnfall-Toolchain/1','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})

def download(asset, folder):
    name=asset['name']; path=folder/name
    digest=asset.get('digest') or ''
    if not digest.startswith('sha256:'):
        raise RuntimeError('The official release did not publish a SHA-256 digest for '+name+'. Refusing an unverified tool download.')
    expected=digest.split(':',1)[1]
    if path.exists() and hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==expected: return path
    partial=path.with_suffix(path.suffix+'.partial')
    with urllib.request.urlopen(request(asset['browser_download_url']),timeout=90) as source, partial.open('wb') as dest:
        shutil.copyfileobj(source,dest,1024*1024)
    with partial.open('rb') as data: actual=hashlib.file_digest(data,'sha256').hexdigest()
    if actual!=expected:
        partial.unlink(missing_ok=True); raise RuntimeError('Official archive checksum mismatch: '+name)
    partial.replace(path); return path

def extract(path, target):
    target.mkdir(parents=True,exist_ok=True); base=target.resolve()
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            destination=(base/member.filename).resolve()
            if not destination.is_relative_to(base): raise ValueError('Archive path escapes its destination.')
            if stat.S_ISLNK(member.external_attr>>16): raise ValueError('Archive symbolic links are not accepted.')
        archive.extractall(target)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--os',choices=['windows','linux'],default='windows' if platform.system()=='Windows' else 'linux'); parser.add_argument('--directory',type=Path,default=Path('.tools')); parser.add_argument('--with-templates',action='store_true')
    args=parser.parse_args(); folder=args.directory.resolve(); folder.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(request(API),timeout=30) as response: release=json.load(response)
    suffix='win64' if args.os=='windows' else 'linux_x86_64'
    name=f'Godot_v{VERSION}-stable_mono_{suffix}.zip'
    asset=next((a for a in release['assets'] if a['name']==name),None)
    if asset is None: raise RuntimeError('The pinned official editor archive is unavailable: '+name)
    archive=download(asset,folder); editor=folder/'godot'; extract(archive,editor)
    candidates=sorted(editor.rglob('*_console.exe')) if args.os=='windows' else sorted(p for p in editor.rglob('Godot*') if p.is_file() and p.name.endswith('.x86_64'))
    if not candidates: raise RuntimeError('The editor executable was not found in the verified archive.')
    binary=candidates[0]
    if args.os=='linux': binary.chmod(binary.stat().st_mode|0o111)
    if args.with_templates:
        target_name=f'Godot_v{VERSION}-stable_mono_export_templates.tpz'
        asset=next((a for a in release['assets'] if a['name']==target_name),None)
        if asset is None: raise RuntimeError('The pinned .NET export templates are unavailable.')
        templates=download(asset,folder); temporary=folder/'export-template-source'; extract(templates,temporary)
        version_files=list(temporary.rglob('version.txt'))
        if len(version_files)!=1: raise RuntimeError('Unexpected export-template version manifest.')
        manifest=version_files[0]; version=manifest.read_text().strip()
        if version!=f'{VERSION}.stable.mono': raise RuntimeError('Unexpected .NET template version: '+version)
        data=Path(os.environ['APPDATA'])/'Godot' if args.os=='windows' else Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'godot'
        dest=data/'export_templates'/version; shutil.copytree(manifest.parent,dest,dirs_exist_ok=True)
        print('Installed verified templates:',dest,flush=True)
    result={'version':VERSION,'binary':str(binary),'official_release':release['html_url']}
    (folder/'godot.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as handle: handle.write('GODOT_BIN='+str(binary)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__': main()
