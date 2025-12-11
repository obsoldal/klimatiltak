import streamlit as st
from bakgrunnsdata import utslippskilder
from beregninger import (
    beregn_aarlig_tiltaksmengde,
    beregn_total_tiltaksmengde,
    beregn_aarlig_utslippsreduksjon,
    beregn_total_utslippsreduksjon,
    beregn_karbonprisjustert_merkostnad,
    beregn_naaverdi,
    beregn_tiltakskostnad
)
from formatering import formater_nummer
from registrer_tiltak import registrer_tiltak, hent_registrerte_tiltak
from visualisering import (
    vis_sammenligning_av_unngaatte_utslipp,
    vis_sammenligning_av_naaverdi,
    vis_sammenligning_av_tiltakskostnad,
    vis_avgiftsbaner,
    vis_totalinvestering
)
from kopier_tiltak import FIELD_MAP, kopier_tiltak

st.set_page_config(
    page_title="Klimatiltak",
    page_icon=":material/globe:"
)

st.title("Klimatiltak")

if 'unik_id' in st.session_state:
    st.success(f"Tiltaket er registrert! *Tiltakets unike ID: {st.session_state['unik_id']}*", icon="✅")
    st.button(
        "Registrer nytt tiltak",
        on_click=lambda: st.session_state.pop('unik_id', None)
    )
    st.stop()

with st.expander("Vis generell informasjon tilknyttet klimatiltaksverktøyet"):
    st.markdown(
        """
        **Forutsetninger for utregning av klimatiltak:** 
        * Godt dokumenterte historiske data og regnskap  
        * Integrerte budsjetterings og rapporteringssystemer  
        * Kontinuerlig vurdering og oppfølging  
        """)
    st.divider()
    st.markdown(
        """
        **Dette verktøyet er begrenset til:**  
        * Forsvarets materiellbeholdning og investeringsportefølje  
        * Klimautslippsrettede bærekraftstiltak  
          * :gray[*For andre bærekraftstiltak og virkemidler benyttes andre verktøy og prosesser.*]  
        * Direkte utslipp (såkalt Scope 1-utslipp)  
          * :gray[*Scope 1-utslipp oppstår som en direkte konsekvens av virksomhetens aktiviteter, primært drivstofforbruk gjennom operativ virksomhet.
             Scope 2- og 3-utslipp oppstår som en indirekte konsekvens av produksjon, strømforsyning og avhending av virksomhetens forbruk og aktivitet.*]
        * Kvantifiserbare CO2-utslipp  
          * :gray[*Kun utslipp av CO2 til luft som kan måles og knyttes til konkrete utslippskilder, som materiell, vil beregnes.*]
        """)

st.subheader("Fyll inn informasjon om tiltaket")

dif = st.selectbox(
    "DIF",
    ("Hæren", "Sjøforsvaret", "Luftforsvaret", "FLO", "Andre"),
    index=None,
    placeholder="Velg DIF",
    key=FIELD_MAP["DIF"],
    help="""
        **Hvilken driftsenhet tilhører du?**  
        Velg fra rullgardinlisten.  
        Representerer du en annen DIF enn de tre alternativene, velg 'Andre'.
    """
)

avdeling = st.text_input(
    "Avdeling",
    placeholder="Fyll inn avdeling",
    key=FIELD_MAP["Avdeling"],
    help="""
        **Hvilken avdeling i driftsenheten tilhører du?**  
        Skriv inn fullt navn på avdelingen.
    """
)

enhet = st.text_input(
    "Enhet",
    placeholder="Fyll inn enhet",
    key=FIELD_MAP["Enhet"],
    help="""
        **Hvem har ansvaret for å følge opp tiltaket?**  
        Skriv inn fullt navn på enheten.
    """
)

beskrivelse = st.text_area(
    "Tiltaksbeskrivelse",
    placeholder="Fyll inn tiltaksbeskrivelse",
    key=FIELD_MAP["Tiltaksbeskrivelse"],
    help="""
        **Hva går tiltaket ut på?**  
        Beskriv tiltaket i en kort tekst (maks 100 ord).
        Beskrivelsen bør inneholde *hva* tiltaket går ut på,
        *hvilke* utslipp tiltaket kan redusere,
        og hvordan tiltaket vil påvirke drift i form av bemannings- og investeringsbehov.
        Ytterligere datagrunnlag kan utdypes i Kolonne D, "Kommentarer".
    """
)

utslippskilde = st.selectbox(
    "Kilde til direkte utslipp",
    list(utslippskilder.keys()),
    index=None,
    placeholder="Velg utslippskilde",
    key=FIELD_MAP["Kilde til direkte utslipp"],
    help="""
        **Hvor oppstår CO2-utslippet?**  
        Velg fra rullgardinlisten.  
        Om tiltaket målrettes drivstofforbrukende aktiviteter, velg 'Fossilt drivstofforbruk'.  
        Om tiltaket målrettes transportrettede aktiviteter, velg 'Personelltransport'.  
        Om tiltaket målrettes energiforbrukende aktiviteter, velg 'Energiforbruk'.  
        Om tiltaket målrettes andre utslippskilder enn disse tre, velg 'Andre' (merk: tiltakseffekter vil ikke beregnes for disse tiltakene).
    """
)

materiell_disabled = True
materiell_options = []
if (utslippskilde and
    'Utslippsfaktor' in utslippskilder[utslippskilde] and
    len(utslippskilder[utslippskilde]['Utslippsfaktor']) >= 1):
    materiell_disabled = False
    materiell_options = list(utslippskilder[utslippskilde]['Utslippsfaktor'].keys())

materiell = st.selectbox(
    "Materiell tilknyttet utslipp",
    materiell_options,
    index=None,
    placeholder="Velg materiell",
    key=FIELD_MAP["Materiell tilknyttet utslipp"],
    disabled=materiell_disabled,
    help="""
        **Hvilke type materiell omhandler tiltaket?**  
        Velg fra rullgardinlisten.  
        Om tiltaket målrettes ulike plattformer og/eller kjøretøy, velg en av dem (verktøyet er beregnet for å lage ett tiltak per materiell-type).  
        Om tiltaket målrettes transportrettede aktiviteter, velg 'Personelltransport'.  
        Om tiltaket målrettes andre utslippspunkter enn materiell, velg 'Andre' (merk: tiltakseffekter vil ikke beregnes for disse tiltakene).
    """
)

st.divider()
st.subheader("Fyll inn estimater for tiltaket")

comment_help = "Beskriv datakilde eller utregningsmetode for estimatet om dette er tilgjengelig."

col1, col2 = st.columns(2, vertical_alignment="bottom")
antall_materiell = col1.number_input(
    "Antall materiell tiltaket målrettes",
    min_value=0,
    key=FIELD_MAP["Antall materiell tiltaket målrettes"],
    help="""
        **Hvor mange enheter materiell påvirkes?**  
        Fyll inn antall materiell som vil påvirkes direkte av tiltaket.
        Dette kan for eksempel innebære antall lette eller tunge kjøretøy som elektrifiseres,
        antallet fartøy som reduserer energiforbruket,
        eller antall luftfartøy som målrettes innblanding av biodrivstoff. 

    """
)
col2.button(
    "*antall*",
    type="tertiary",
    disabled=True,
    key="antall_enhet"
)
antall_materiell_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til antall materiell",
    key=FIELD_MAP["Kommentar antall materiell"],
    help=comment_help
)

col1, col2 = st.columns(2, vertical_alignment="bottom")
forbruk = col1.number_input(
    "Materiellets nåværende forbruk",
    min_value=0,
    key=FIELD_MAP["Materiellets nåværende forbruk"],
    help="""
        **Hva forbruker dette materiellet i dag, per år i angitt enhet?**  
        Fyll inn absolutt mengde som forbrukes av det angitte materielelt basert på egne estimater eller regnskapsført tall for 2024.
        Dersom materiellets forbruk er ukjent eller ikke beregnet, før inn sjablongmessige tall basert på sammenliknbart materiell eller sivilt materiell. 
    """
    )
col2.button(
    f"*{utslippskilder[utslippskilde]['Forbruk enhet']}*" if utslippskilde else "*(Velg utslippskilde for å definere enhet)*",
    type="tertiary",
    disabled=True,
    key="forbruk_enhet"
)
forbruk_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til nåværende forbruk",
    key=FIELD_MAP["Kommentar nåværende forbruk"],
    help=comment_help
)

col1, col2 = st.columns(2, vertical_alignment="bottom")
reduksjon_absolutt = col1.number_input(
    "Årlig reduksjon etter tiltaket (absolutt)",
    min_value=0,
    key=FIELD_MAP["Årlig reduksjon etter tiltaket (absolutt)"],
    help="""
        **Hvor mye kan tiltaket redusere i absolutte mengde, per materiell og per år?**  
        Fyll inn absolutt mengde som endres basert på egne estimater eller regnskapsført tall for 2024.
    """
)
col2.button(
    f"*{utslippskilder[utslippskilde]['Reduksjon enhet']}*" if utslippskilde else "*(Velg utslippskilde for å definere enhet)*",
    type="tertiary",
    disabled=True,
    key="reduksjon_absolutt_enhet"
)
col1, col2 = st.columns(2, vertical_alignment="bottom")
reduksjon_prosent = col1.number_input(
    "Årlig reduksjon etter tiltaket (prosent)",
    min_value=0,
    max_value=100,
    key=FIELD_MAP["Årlig reduksjon etter tiltaket (prosent)"],
    help="""
        **Hvor stor andel av dagens mengde kan reduseres, per materiell og per år?**  
        Fyll inn andelen av forbruket som forventes redusert ved tiltaket. Fylles bare inn dersom absolutt mengde er ukjent.
    """,
    disabled=reduksjon_absolutt > 0
)
col2.button(
    "*prosentvis reduksjon*",
    type="tertiary",
    disabled=True,
    key="reduksjon_prosent_enhet"
)
reduksjon_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til årlig reduksjon",
    key=FIELD_MAP["Kommentar årlig reduksjon"],
    help=comment_help
)

col1, col2 = st.columns(2, vertical_alignment="bottom")
engangsinvestering = col1.number_input(
    "Forventet engangsinvestering",
    min_value=0,
    key=FIELD_MAP["Forventet engangsinvestering [NOK]"],
    help="""
        **Hva vil tiltaket kreve av nye midler over investeringsbudsjettet?**  
        Fyll inn estimat for engangsinvestering (typisk første året) basert på deres beregning eller en sammenlikning med tilsvarende investeringer
    """
)
col2.button(
    "*NOK, år 0*",
    type="tertiary",
    disabled=True,
    key="engangsinvestering_enhet"
)
engangsinvestering_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til engangsinvestering",
    key=FIELD_MAP["Kommentar engangsinvestering"],
    help=comment_help
)

col1, col2 = st.columns(2, vertical_alignment="bottom")
merkostnad = col1.number_input(
    "Forventet merkostnad (MK)",
    step=1,
    key=FIELD_MAP["Forventet merkostnad (MK) [NOK/år]"],
    help="""
        **Hva vil tiltaket medføre i netto driftskostnader?**  
        Fyll inn summen av forventede årlige utgifter eller besparelser i drift ved gjennomføring av tiltaket, basert på egne beregninger eller tidligere driftregnskap.
        Økninger i driftsutgifter angis med positivt fortegn (+), mens besparelser angis med negativt fortegn (-).
    """
)
col2.button(
    "*NOK, årlig*",
    type="tertiary",
    disabled=True,
    key="merkostnad_enhet"
)
merkostnad_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til merkostnad",
    key=FIELD_MAP["Kommentar merkostnad"],
    help=comment_help
)

col1, col2 = st.columns(2, vertical_alignment="bottom")
levetid = col1.number_input(
    "Tiltakets levetid",
    min_value=1,
    max_value=12,
    key=FIELD_MAP["Tiltakets levetid [år]"],
    help="""
        **Hvor lenge er tiltaket anslått å vare, i antall år?**  
        Fyll inn antall år mellom 1 og 12.
        For tiltak som forventes å vare lenger enn 12 år, fyll inn 12 og kommenter estimert levetid i Kolonne D (tallet vil ikke påvirke resultatet utover beregning av investeringsbeløpets nåverdi)
    """
)
col2.button(
    "*antall år*",
    type="tertiary",
    disabled=True,
    key="levetid_enhet"
)
levetid_kommentar = st.text_area(
    "Kommentar",
    placeholder="Fyll inn kommentar til levetid",
    key=FIELD_MAP["Kommentar levetid"],
    help=comment_help
)

ikke_kvantifiserte_effekter = st.text_area(
    "Ikke-kvantifiserte effekter",
    placeholder="Fyll inn beskrivelse av ikke-kvantifiserte effekter",
    key=FIELD_MAP["Ikke-kvantifiserte effekter"],
    help="""
        **Hvilke andre effekter er relevant å vurdere ved gjennomføring av tiltaket?**  
        Beskriv andre effekter, f.eks. hvordan tiltaket kan påvirke beredskap og/eller operativ evne.
    """
)

with st.sidebar:
    st.header("Beregnet tiltakseffekt")

    tiltaksmengde_enhet = utslippskilder[utslippskilde]['Reduksjon enhet'] if utslippskilde else "(Velg utslippskilde for å definere enhet)"
    
    aarlig_tiltaksmengde = beregn_aarlig_tiltaksmengde(antall_materiell, forbruk, reduksjon_absolutt, reduksjon_prosent)
    st.markdown(
        f"Årlig tiltaksmengde:  \n**:blue[{formater_nummer(aarlig_tiltaksmengde)}]** *:gray[{tiltaksmengde_enhet}]*",
        help="""**Mengden tiltaket vil påvirke årlig**  
            :blue-badge[Antall materiell tiltaket målrettes] x :blue-badge[Årlig reduksjon etter tiltaket (absolutt)]  
            *eller*  
            :blue-badge[Antall materiell tiltaket målrettes] x :blue-badge[Materiellets nåværende forbruk] x :blue-badge[Årlig reduksjon etter tiltaket (prosent)]
        """
    )

    total_tiltaksmengde = beregn_total_tiltaksmengde(aarlig_tiltaksmengde, levetid)
    st.markdown(
        f"Total tiltaksmengde:  \n**:blue[{formater_nummer(total_tiltaksmengde)}]** *:gray[{tiltaksmengde_enhet}]*",
        help="""**Mengden tiltaket vil påvirke totalt, gjennom levetiden**  
            :blue-badge[Årlig tiltaksmengde] x :blue-badge[Tiltakets levetid]
        """
    )

    aarlig_utslippsreduksjon = beregn_aarlig_utslippsreduksjon(aarlig_tiltaksmengde, utslippskilde, materiell)
    st.markdown(
        f"Unngåtte utslipp, årlig:  \n**:blue[{formater_nummer(aarlig_utslippsreduksjon/1000, 1)}]** *:gray[tonn CO2-ekv. per år]*",
        help="""**Hvor mange tonn CO2-utslipp vil tiltaket kunne redusere årlig?**  
            :blue-badge[Årlig tiltaksmengde] x :blue-badge[Utslippsfaktor for valgt utslippskilde og materiell]
        """
    )

    total_utslippsreduksjon = beregn_total_utslippsreduksjon(aarlig_utslippsreduksjon, levetid)
    st.markdown(
        f"Unngåtte utslipp, totalt:  \n**:blue[{formater_nummer(total_utslippsreduksjon/1000, 1)}]** *:gray[tonn CO2-ekv.]*",
        help="""**Hvor mange tonn CO2-utslipp vil tiltaket redusere totalt?**  
            :blue-badge[Unngåtte utslipp, årlig] x :blue-badge[Tiltakets levetid]
        """
    )

    karbonprisjustert_merkostnad_foerste_aar = beregn_karbonprisjustert_merkostnad(aarlig_utslippsreduksjon, 2026, merkostnad)
    st.markdown(
        f"Karbonprisjustert MK, første år:  \n**:blue[{formater_nummer(karbonprisjustert_merkostnad_foerste_aar)}]** *:gray[NOK, år 1]*",
        help="""**Hva blir årlig driftskonsekvens justert for CO2-avgiftssatser i år 1?**  
            :blue-badge[Forventet merkostnad (MK)] - (:blue-badge[Unngåtte utslipp, årlig] x :blue-badge[Neste års CO2-avgift])
        """
    )

    karbonprisjustert_merkostnad_siste_aar = beregn_karbonprisjustert_merkostnad(aarlig_utslippsreduksjon, 2025 + levetid, merkostnad)
    if levetid > 1:
        st.markdown(
            f"Karbonprisjustert MK, siste år:  \n**:blue[{formater_nummer(karbonprisjustert_merkostnad_siste_aar)}]** *:gray[NOK, år {levetid}]*",
            help="""**Hva blir årlig driftskonsekvens justert for CO2-avgiftssatser i siste år av tiltakets levetid?**  
                :blue-badge[Forventet merkostnad (MK)] - (:blue-badge[Unngåtte utslipp, årlig] x :blue-badge[CO2-avgift i siste år av tiltakets levetid])
            """
        )

    naaverdi = beregn_naaverdi(aarlig_utslippsreduksjon, merkostnad, levetid, engangsinvestering)
    st.markdown(
        f"Tiltakets nåverdi:  \n**:blue[{formater_nummer(naaverdi)}]** *:gray[NOK, år 0]*",
        help="""**Hva er tiltakets netto nåverdi, gitt fremtidige karbonpriser og driftskonsekvenser?**  
            :blue-badge[Forventet engangsinvestering] + Summen av :blue-badge[Karbonprisjustert MK, år *n*] / :blue-badge[1.04^*n*] for hvert år *n* i tiltakets levetid
        """
    )

    tiltakskostnad = beregn_tiltakskostnad(total_utslippsreduksjon/1000, naaverdi)
    st.markdown(
        f"Tiltakskostnad:  \n**:blue[{formater_nummer(tiltakskostnad)}]** *:gray[NOK per tonn CO2-ekv.]*",
        help="""**Hva er tiltakets kostnadseffektivitet gitt antall unngåtte utslipp per krone?**  
            :blue-badge[Tiltakets nåverdi] / :blue-badge[Unngåtte utslipp, totalt]
        """
    )

data = [
    dif,
    avdeling,
    enhet,
    beskrivelse,
    utslippskilde,
    materiell,
    antall_materiell,
    antall_materiell_kommentar,
    forbruk,
    forbruk_kommentar,
    reduksjon_absolutt,
    reduksjon_prosent,
    reduksjon_kommentar,
    engangsinvestering,
    engangsinvestering_kommentar,
    merkostnad,
    merkostnad_kommentar,
    levetid,
    levetid_kommentar,
    ikke_kvantifiserte_effekter,
    aarlig_tiltaksmengde,
    total_tiltaksmengde,
    aarlig_utslippsreduksjon,
    total_utslippsreduksjon,
    karbonprisjustert_merkostnad_foerste_aar,
    karbonprisjustert_merkostnad_siste_aar,
    naaverdi,
    tiltakskostnad
]

with st.sidebar:
    st.header("Send inn utfylt skjema")
    st.button(
        "Registrer tiltaket",
        type="primary",
        help="Klikk for å registrere tiltaket i databasen",
        on_click=registrer_tiltak,
        args=(data,),
        icon=":material/assignment_add:"
    )

st.divider()
st.subheader("Støttefunksjonalitet")

tab1, tab2, tab3, tab4 = st.tabs([
    "Avgiftsbaner",
    "Totalinvestering",
    "Sammenligning av tiltak",
    "Registrerte tiltak"
])

with tab1:
    vis_avgiftsbaner(aarlig_utslippsreduksjon, merkostnad)

with tab2:
    vis_totalinvestering(aarlig_utslippsreduksjon, merkostnad, engangsinvestering)

registrerte_tiltak = hent_registrerte_tiltak()
with tab3:
    sammenligning = st.multiselect(
        "Velg tiltak du ønsker å sammenligne med",
        registrerte_tiltak["Tiltaksnummer"].dropna().tolist(),
        placeholder="Velg ett eller flere tiltak",
        format_func=lambda x: f"Tiltak {x}",
        help="Velg ett eller flere tidligere registrerte tiltak for å sammenligne med det nye tiltaket"
    )
    if sammenligning:
        vis_sammenligning_av_unngaatte_utslipp(total_utslippsreduksjon, sammenligning, registrerte_tiltak)
        vis_sammenligning_av_naaverdi(naaverdi, sammenligning, registrerte_tiltak)
        vis_sammenligning_av_tiltakskostnad(tiltakskostnad, sammenligning, registrerte_tiltak)

with tab4:
    st.markdown("**Oversikt over tidligere registrerte tiltak**")
    st.dataframe(registrerte_tiltak, hide_index=True)
    st.button(
        "Oppdater oversikten",
        on_click=lambda: st.cache_data.clear(),
        icon=":material/refresh:"
    )
    st.caption("Alle registrerte tiltak lagres her: https://docs.google.com/spreadsheets/d/1FLDZ9ZibMww44XnBYChb-ecOTvD189TR-vZ6QpGREnM/edit?usp=sharing")
    st.markdown("**Ønsker du å kopiere inndata fra et tidligere registrert tiltak?**")
    tiltaksnummer_kopiering = st.selectbox(
        "Tiltak",
        registrerte_tiltak["Tiltaksnummer"].dropna().tolist(),
        index=None,
        placeholder="Velg tiltak",
        format_func=lambda x: f"Tiltak {x}",
        label_visibility="collapsed"
    )
    kopieringstiltak_valgt = False
    if tiltaksnummer_kopiering:
        kopieringstiltak_valgt = True
    st.button(
        "Kopier inndata fra valgt tiltak",
        disabled=not kopieringstiltak_valgt,
        icon=":material/content_copy:",
        on_click=kopier_tiltak,
        args=(tiltaksnummer_kopiering, registrerte_tiltak)
    )
    st.caption("Advarsel: Ved kopiering vil alle data du allerede har fylt inn i skjemaet over bli overskrevet.")
