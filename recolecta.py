#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import threading
import requests as req
import json
import Queue
from filtro import Filtro


class Recolector(threading.Thread):
    """Realiza las peticiones
    """
    headers = {"Content-Type": "application/json; charset=UTF-8",
               "Accept": "application/json"}
    base_url = "http://200.48.102.67/pecaoe/servicios/"
    dic_urls = {
        "principal": (base_url + "declaracion.asmx/" +
                      "CandidatoListarPorID"),
        "familia": (base_url + "declaracion.asmx/" +
                    "CandidatoFamiliaListarPorCandidato"),
        "otra_experiencia": (base_url + "declaracion.asmx/" +
                             "CandidatoAdicionalListarPorCandidato"),
        "observaciones": (base_url + "simulador.asmx/" +
                          "Soporte_CandidatoAnotMarginal"),
        "ingresos": (base_url + "declaracion.asmx/" +
                     "IngresoListarPorCandidato"),
        "experiencia": (base_url + "declaracion.asmx/" +
                        "CandidatoExperienciaListarPorCandidato"),
        "educacion_superior": (base_url + "declaracion.asmx/" +
                               "EducacionSuperiorListarPorCandidato"),
        "educacion_basica": (base_url + "declaracion.asmx/" +
                             "EducacionBasicaListarPorCandidato"),
        "militancia": (base_url + "declaracion.asmx/" +
                       "RenunciasOPListarPorCandidato"),
        "eleccion": (base_url + "declaracion.asmx/" +
                     "CargoEleccionListarPorCandidato"),
        "partidario": (base_url + "declaracion.asmx/" +
                       "CargoPartidarioListarPorCandidato"),
        "bienes": (base_url + "declaracion.asmx/" +
                   "BienesListarPorCandidato"),
        "penal": (base_url + "declaracion.asmx/" +
                  "AmbitoPenalListarPorCandidato"),
        "civil": (base_url + "declaracion.asmx/" +
                  "AmbitoCivilListarPorCandidato"),
        "acreencias": (base_url + "declaracion.asmx/" +
                       "EgresosListarPorCandidato"),
    }

    def __init__(self, maestro):
        threading.Thread.__init__(self)
        # Puede variar
        self.maestro = maestro

    def genera_payload(self, id_Candidato):
        return {
            "objCandidatoBE": {
                "objProcesoElectoralBE": {
                    "intIdProceso": "72"},
                "objOpInscritasBE": {
                    "intCod_OP": "140"},
                "intId_Candidato": str(id_Candidato)}
        }

    def realiza_peticion(self, key, id_candidato, payload):
        """Realiza una peticion, devuelve la respuesta (json) como
        un diccionario"""
        url = self.dic_urls[key]
        # Realiza la peticion, intenta hasta que funcione
        while True:
            try:
                r = req.post(url,
                             data=json.dumps(payload),
                             headers=self.headers,
                             timeout=1)
            except req.Timeout:
                self.maestro.imprime("Hilo:Timeout error")
                continue
            except req.ConnectionError as error:
                errno = error.errno
                err_msg_list = ["Hilo: ConnectionError", errno]
                if errno == 101:
                    err_msg_list.append(":: Esta conectado a internet?")
                if errno == 104:
                    err_msg_list.append(":: Connection reset by peer")
                self.maestro.imprime(err_msg_list)
                continue
            except Exception as e:
                self.maestro.imprime("hilo: Error", e)
                continue
            else:
                return r.json()

    def descarga_candidato(self, id_candidato):
        """Descarga los datos y los filtra

        Si es un id valido, devuelve un diccionario de los datos.
        En caso contrario devuelve None"""
        dic_candidato = {"id": id_candidato}
        cont = self.genera_payload(id_candidato)
        # Verifica si el id es valido
        j_principal = self.realiza_peticion(
            "principal", id_candidato, cont)

        d_principal = getattr(Filtro, "f_principal")(j_principal)
        if (not d_principal):
            return None
        else:
            dic_candidato["principal"] = d_principal

        for k in self.dic_urls.keys():
            if k == "principal":
                continue
            j_dato = self.realiza_peticion(k, id_candidato, cont)
            dic_candidato[k] = getattr(Filtro, "f_"+k)(j_dato)

        return dic_candidato

    def run(self):
        while True:
            try:
                task = self.maestro.get_task()
                self.maestro.imprime("Tarea obtenida", task)
                datos = self.descarga_candidato(*task)
                self.maestro.put_task(datos)
            except StopIteration:
                self.maestro.imprime("Hilo: Terminado")
                break

    @staticmethod
    def put_task(dic_datos):
        print dic_datos
