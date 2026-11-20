import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Le Bureau des Lutins 🎄", page_icon="🎁", layout="centered")
st.markdown("""<style>
.stApp {background:#fffaf3;color:#283c30}
h1,h2,h3 {color:#245340!important}
[data-testid="stSidebar"] {background:#48514f;color:#fff}
[data-testid="stSidebar"] * {color:#fff!important}
[data-testid="stSidebar"] button {background:#384a46!important;border:1px solid #e5e5e5!important}
[data-testid="stSidebar"] button * {color:#fff!important}
[data-testid="stSidebar"] input {color:#fff!important}
[data-testid="stAppViewContainer"] [data-testid="stAlert"] a,
[data-testid="stAppViewContainer"] a {color:#155f4b}
[data-testid="stAppViewContainer"] [data-testid="stAlert"] {color:#203b35}
.stTabs [data-baseweb="tab-list"] {background:#444f4b;border-radius:9px;padding:4px}
.stTabs [data-baseweb="tab"] {color:#fff!important}
.stTabs [data-baseweb="tab"] * {color:#fff!important}
.stTabs [data-baseweb="tab"][aria-selected="true"] {background:#6d8178}
div[data-baseweb="select"] > div, div[data-baseweb="popover"] {color:#fff}
div[data-baseweb="select"] > div * {color:#fff!important}
div[data-baseweb="popover"] * {color:#fff!important}
[data-testid="stExpander"] summary {background:#58625f;color:#fff!important}
[data-testid="stExpander"] summary * {color:#fff!important}
[data-testid="stWidgetLabel"] p {color:#253f34!important}
.stButton button[kind="secondary"] {background:#53655c;color:#fff!important;border-color:#53655c}
.stButton button[kind="secondary"] * {color:#fff!important}
.stLinkButton a {background:#53655c;color:#fff!important;border-color:#53655c}
.stLinkButton a * {color:#fff!important}
.stButton button[kind="primary"] {background:#a92335;border-color:#a92335}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

def call(name, **params):
    return db().rpc(name, params).execute().data

def reload_board():
    st.session_state.board = call("lutin_board", p_code=st.session_state.code)
    try:
        st.session_state.collectives = call("lutin_collectives", p_code=st.session_state.code)
        st.session_state.collectives_ready = True
    except Exception:
        # La V1 continue de fonctionner tant que migration_v2.sql n'est pas appliquée.
        st.session_state.collectives = []
        st.session_state.collectives_ready = False

def action(name, **params):
    try:
        call(name, p_code=st.session_state.code, **params)
        reload_board()
        st.rerun()
    except Exception as exc:
        st.error(f"Le serveur des lutins proteste : {exc}")

st.title("🎄 Le Bureau des Lutins")
st.caption("Des listes, des surprises et zéro cadeau en double !")
st.caption("📂 Dépôt GitHub : ceciledehosson/bureau-des-lutins")
st.caption("© 2026 Cécile de Hosson — Tous droits réservés.")

if "code" not in st.session_state:
    with st.form("login"):
        code = st.text_input("Ton code secret de lutin", type="password")
        sent = st.form_submit_button("Entrer dans l'atelier 🎅", type="primary")
    if sent:
        try:
            normalized = code.strip()
            identity = call("lutin_identity", p_code=normalized)
            if identity:
                st.session_state.code = normalized
                reload_board()
                st.rerun()
            else:
                st.error("Code inconnu du Père Noël !")
        except Exception as exc:
            st.error(f"Connexion impossible : {exc}")
    st.stop()

if "board" not in st.session_state:
    reload_board()
board = st.session_state.board
me = board["me"]
people = {m["id"]: m["name"] for m in board["members"]}
collectives = {c["wish_id"]: c for c in st.session_state.get("collectives", [])}
collectives_ready = st.session_state.get("collectives_ready", False)

with st.sidebar:
    st.header(f"🧝 Bonjour {people.get(me, 'Lutin')} !")
    if st.button("🔄 Actualiser les listes", use_container_width=True):
        reload_board()
        st.rerun()
    if st.button("🚪 Quitter l'atelier", use_container_width=True):
        st.session_state.pop("code", None)
        st.session_state.pop("board", None)
        st.rerun()
    st.caption("Chut ! Tu ne verras jamais les réservations sur ta propre liste.")

letter, workshop, sleigh = st.tabs(["💌 Ma lettre", "🎁 L'atelier", "🛷 Ma hotte"])
priorities = ["Ça me ferait plaisir", "J’en rêve", "Si le Père Noël est riche"]

with letter:
    st.subheader("Ma lettre au Père Noël")
    st.write("Ajoute tes envies : les autres lutins peuvent les réserver en secret.")
    with st.expander("➕ Ajouter une envie"):
        with st.form("new_wish", clear_on_submit=True):
            title = st.text_input("Le cadeau *", max_chars=180)
            details = st.text_area("Quelques précisions", max_chars=1500)
            price = st.number_input("Prix indicatif (€)", min_value=0.0, step=1.0)
            unknown = st.checkbox("Prix inconnu")
            url = st.text_input("Lien (facultatif)", max_chars=1000)
            priority = st.selectbox("Priorité", priorities)
            submitted = st.form_submit_button("Envoyer au Père Noël 🎅", type="primary")
        if submitted:
            if not title.strip() or (url and not url.startswith(("https://", "http://"))):
                st.warning("Indique un cadeau et, s'il y a un lien, commence-le par https://")
            else:
                action("lutin_save_wish", p_title=title.strip(), p_details=details,
                       p_price=None if unknown else price, p_url=url, p_priority=priority)
    own = [w for w in board["wishes"] if w["owner_id"] == me]
    if not own:
        st.info("Ta lettre est encore vide. Les lutins attendent !")
    for w in own:
        with st.expander(f"🎄 {w['title']} — {w['priority']}"):
            st.write(w["details"] or "Aucune précision")
            st.caption(f"Prix indicatif : {w['price']} €" if w["price"] is not None else "Prix inconnu")
            if w["url"].startswith(("https://", "http://")):
                st.link_button("Voir le lien", w["url"])
            st.caption("Impossible de savoir si ce cadeau a été réservé. Surprise ! 🤫")
            with st.form(f"edit_{w['id']}"):
                t = st.text_input("Nom du cadeau", value=w["title"])
                d = st.text_area("Précisions", value=w["details"])
                p = st.number_input("Prix (€)", min_value=0.0, value=float(w["price"] or 0),
                                    key=f"p_{w['id']}")
                unk = st.checkbox("Prix inconnu", value=w["price"] is None, key=f"unk_{w['id']}")
                u = st.text_input("Lien", value=w["url"])
                pri = st.selectbox("Priorité", priorities, index=priorities.index(w["priority"]))
                save = st.form_submit_button("Enregistrer")
            if save:
                if not t.strip() or (u and not u.startswith(("https://", "http://"))):
                    st.warning("Vérifie le titre et le lien.")
                else:
                    action("lutin_save_wish", p_id=w["id"], p_title=t.strip(),
                           p_details=d, p_price=None if unk else p, p_url=u, p_priority=pri)
            if st.button("🗑️ Supprimer", key=f"delete_{w['id']}"):
                action("lutin_delete_wish", p_id=w["id"])

with workshop:
    st.subheader("L'atelier des lutins")
    if not collectives_ready:
        st.caption("🎁 Les cadeaux collectifs seront disponibles après l'installation de la mise à jour Supabase.")
    others = [m for m in board["members"] if m["id"] != me]
    if others:
        person = st.selectbox("À qui veux-tu faire plaisir ?", [m["name"] for m in others])
        pid = next(m["id"] for m in others if m["name"] == person)
        gifts = [w for w in board["wishes"] if w["owner_id"] == pid]
        if not gifts:
            st.info("Aucune envie pour le moment : ce lutin réfléchit encore.")
        for w in gifts:
            r = w["reservation"]
            with st.container(border=True):
                st.markdown(f"#### 🎁 {w['title']}")
                st.write(w["details"] or "")
                st.caption(f"{w['priority']} · " +
                           (f"environ {w['price']} €" if w["price"] is not None else "prix inconnu"))
                if w["url"].startswith(("https://", "http://")):
                    st.link_button("🔗 Voir le cadeau", w["url"])
                if r is None:
                    if st.button("Je m'en occupe ! 🎅", key=f"reserve_{w['id']}", type="primary"):
                        action("lutin_reserve", p_wish_id=w["id"], p_action="reserve")
                else:
                    collective = collectives.get(w["id"], {})
                    participants = collective.get("participants", [])
                    my_part = next((p for p in participants if p["member_id"] == me), None)
                    if r["member_id"] == me:
                        st.success(f"Tu coordonnes ce cadeau · {r['status']}")
                        a, b = st.columns(2)
                        if r["status"] != "Acheté" and a.button("✅ Acheté", key=f"buy_{w['id']}"):
                            action("lutin_reserve", p_wish_id=w["id"], p_action="buy")
                        if b.button("↩️ Libérer", key=f"free_{w['id']}",
                                    disabled=bool(participants)):
                            action("lutin_reserve", p_wish_id=w["id"], p_action="release")
                        if participants:
                            st.caption("Demande aux participants de se retirer avant de libérer ce cadeau.")
                    else:
                        st.info(f"🎁 Cadeau coordonné par {people.get(r['member_id'],'un lutin')}.")
                    if collectives_ready:
                        if participants:
                            st.markdown("**Les lutins associés :**")
                            for p in participants:
                                amount = (f" · {p['amount']} €" if p["amount"] is not None
                                          else " · montant à convenir")
                                st.write(f"🧝 {people.get(p['member_id'], 'Un lutin')}{amount}")
                        if r["member_id"] != me:
                            with st.form(f"join_{w['id']}"):
                                st.write("🤝 " + ("Modifier ma participation" if my_part
                                               else "Participer à ce cadeau"))
                                amount_known = st.checkbox("Je précise ma contribution (€)",
                                    value=bool(my_part and my_part["amount"] is not None))
                                amount = st.number_input("Ma participation (€)",
                                    min_value=1.0, value=float(my_part["amount"])
                                    if my_part and my_part["amount"] is not None else 10.0,
                                    step=1.0, disabled=not amount_known,
                                    key=f"amt_{w['id']}")
                                join = st.form_submit_button("🎁 " +
                                    ("Mettre à jour" if my_part else "Rejoindre le cadeau"))
                            if join:
                                action("lutin_contribute", p_wish_id=w["id"],
                                       p_action="join",
                                       p_amount=amount if amount_known else None)
                            if my_part and st.button("Retirer ma participation",
                                                       key=f"leave_{w['id']}"):
                                action("lutin_contribute", p_wish_id=w["id"],
                                       p_action="leave")

with sleigh:
    st.subheader("Ma hotte personnelle 🛷")
    mine = board["my_reservations"]
    if not mine:
        st.info("Hotte vide : mission de lutin encore à accomplir !")
    for r in mine:
        st.write(f"🎁 **{r['title']}** — pour **{r['owner_name']}** · {r['status']}")
    shared = [c for c in collectives.values()
              for p in c.get("participants", []) if p["member_id"] == me]
    if shared:
        st.markdown("#### 🤝 Mes participations collectives")
        for c in shared:
            wish = next((w for w in board["wishes"] if w["id"] == c["wish_id"]), None)
            part = next(p for p in c["participants"] if p["member_id"] == me)
            if wish:
                st.write(f"🎁 **{wish['title']}** — pour **{people.get(wish['owner_id'],'un lutin')}**"
                         + (f" · {part['amount']} €" if part["amount"] is not None
                            else " · contribution à convenir"))
    st.caption("La personne qui coordonne le cadeau gère l'achat ; "
               "les participants fixent entre eux leurs modalités de règlement.")

st.divider()
st.caption("❄️ Le Bureau des Lutins · Noël 2026 · Pas deux fois le même grille-pain.")
