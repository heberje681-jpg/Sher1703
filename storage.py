"""Persistencia. Con secrets de GitHub guarda en la rama 'datos' del repo
(sobrevive a reinicios y no redespliega la app). Sin secrets usa .datos/ (se borra al reiniciar)."""
import json
from pathlib import Path

import requests
import streamlit as st

API = "https://api.github.com"


class _Local:
    persistente = False

    def __init__(self):
        self.raiz = Path(".datos")

    def listar(self, carpeta):
        d = self.raiz / carpeta
        return sorted(p.name for p in d.iterdir()) if d.exists() else []

    def leer(self, ruta):
        p = self.raiz / ruta
        return p.read_bytes() if p.exists() else None

    def escribir(self, ruta, datos):
        p = self.raiz / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(datos)


class _GitHub:
    persistente = True

    def __init__(self, token, repo, rama, base):
        self.repo, self.rama, self.base = repo, rama, base
        self.h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        self._asegurar_rama()

    def _asegurar_rama(self):
        ref = f"{API}/repos/{self.repo}/git/ref/heads/"
        if requests.get(ref + self.rama, headers=self.h, timeout=20).status_code == 200:
            return
        b = requests.get(ref + self.base, headers=self.h, timeout=20)
        b.raise_for_status()
        c = requests.post(f"{API}/repos/{self.repo}/git/refs", headers=self.h, timeout=20,
                          json={"ref": f"refs/heads/{self.rama}", "sha": b.json()["object"]["sha"]})
        c.raise_for_status()

    def _url(self, ruta):
        return f"{API}/repos/{self.repo}/contents/{ruta}"

    def listar(self, carpeta):
        r = requests.get(self._url(carpeta), headers=self.h, params={"ref": self.rama}, timeout=20)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return sorted(i["name"] for i in r.json() if i["type"] == "file")

    def leer(self, ruta):
        h = {**self.h, "Accept": "application/vnd.github.raw+json"}
        r = requests.get(self._url(ruta), headers=h, params={"ref": self.rama}, timeout=60)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content

    def escribir(self, ruta, datos):
        import base64
        for _ in range(3):
            g = requests.get(self._url(ruta), headers=self.h, params={"ref": self.rama}, timeout=20)
            cuerpo = {"message": f"datos: {ruta}", "branch": self.rama,
                      "content": base64.b64encode(datos).decode()}
            if g.status_code == 200:
                cuerpo["sha"] = g.json()["sha"]
            p = requests.put(self._url(ruta), headers=self.h, json=cuerpo, timeout=60)
            if p.status_code in (200, 201):
                return
            if p.status_code not in (409, 422):
                break
        p.raise_for_status()


@st.cache_resource
def obtener():
    try:
        cfg = st.secrets["github"]
        token, repo = cfg["token"], cfg["repo"]
    except Exception:
        return _Local()
    return _GitHub(token, repo, cfg.get("rama", "datos"), cfg.get("rama_base", "main"))


@st.cache_data(ttl=20, show_spinner=False)
def leer_json(ruta, defecto):
    crudo = obtener().leer(ruta)
    return json.loads(crudo) if crudo else defecto


def guardar_json(ruta, obj):
    obtener().escribir(ruta, json.dumps(obj, ensure_ascii=False, indent=1).encode())
    leer_json.clear()


@st.cache_data(ttl=20, show_spinner=False)
def listar_fotos():
    return sorted(obtener().listar("fotos"), reverse=True)


@st.cache_data(ttl=3600, show_spinner=False)
def bytes_foto(nombre):
    return obtener().leer(f"fotos/{nombre}")


def guardar_foto(nombre, datos):
    obtener().escribir(f"fotos/{nombre}", datos)
    listar_fotos.clear()
