"""
Management command to seed the database with sample Ethiopian news articles.

Usage:
    python manage.py seed_articles
    python manage.py seed_articles --clear   # wipe existing data first
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from core.models import Article, Category

CATEGORIES = [
    {"name": "Ethiopia",   "color": "green"},
    {"name": "Africa",     "color": "yellow"},
    {"name": "World",      "color": "blue"},
    {"name": "Business",   "color": "purple"},
    {"name": "Technology", "color": "indigo"},
    {"name": "Sports",     "color": "orange"},
    {"name": "Culture",    "color": "pink"},
]

# picsum.photos with a fixed seed gives a consistent image for each article.
def img(seed, w=800, h=500):
    return f"https://picsum.photos/seed/{seed}/{w}/{h}"


ARTICLES = [
    # --- Featured ---
    {
        "title": "Ethiopia Launches Ambitious Grand Renaissance Dam as East Africa's Largest Power Project",
        "category": "Ethiopia",
        "is_featured": True,
        "is_breaking": False,
        "summary": (
            "After years of construction and diplomatic negotiations, Ethiopia has officially "
            "inaugurated the Grand Ethiopian Renaissance Dam on the Blue Nile, positioning the "
            "country as a major energy exporter across East Africa."
        ),
        "content": (
            "ADDIS ABABA — Ethiopia has officially inaugurated the Grand Ethiopian Renaissance Dam "
            "(GERD), marking a watershed moment for the nation's energy independence and economic "
            "ambitions. The dam, sitting on the Blue Nile river in the Benishangul-Gumuz region, "
            "has a projected capacity of 6,450 megawatts — making it the largest hydroelectric "
            "power plant on the African continent.\n\n"
            "Speaking at the inauguration ceremony, the Prime Minister underscored that the dam "
            "represents 'not just electricity, but sovereignty, pride, and the promise of a better "
            "life for 120 million Ethiopians.' The project, which began in 2011, was financed "
            "entirely through domestic bonds and public contributions.\n\n"
            "The dam is expected to generate enough electricity to power millions of homes across "
            "Ethiopia and export surplus energy to Djibouti, Sudan, and Kenya under existing "
            "regional power-sharing agreements.\n\n"
            "Egypt and Sudan, both downstream Nile nations, have raised concerns about the dam's "
            "potential impact on their water supply. Negotiations facilitated by the African Union "
            "are ongoing, with all three countries committed to reaching a legally binding "
            "agreement on the dam's operation."
        ),
        "image_seed": "gerd-dam",
        "days_ago": 0,
    },
    # --- Breaking ---
    {
        "title": "African Union Emergency Summit Convenes in Addis Ababa Over Horn of Africa Crisis",
        "category": "Africa",
        "is_featured": False,
        "is_breaking": True,
        "summary": (
            "Leaders of 55 African Union member states have gathered for an emergency summit in "
            "Addis Ababa to address escalating security and humanitarian challenges across the "
            "Horn of Africa region."
        ),
        "content": (
            "ADDIS ABABA — The African Union Chairperson has convened an emergency summit of "
            "heads of state at the AU headquarters in Addis Ababa, as security conditions in "
            "parts of the Horn of Africa deteriorate sharply.\n\n"
            "The summit will focus on cross-border security cooperation, the humanitarian "
            "corridor for displaced populations, and renewed calls for a ceasefire in "
            "conflict-affected areas. The AU Commissioner for Peace and Security briefed "
            "delegates on the scale of the crisis, noting that over 2 million people are "
            "currently displaced.\n\n"
            "International partners including the UN, EU, and US have pledged logistical "
            "and financial support for the summit's outcomes."
        ),
        "image_seed": "au-summit",
        "days_ago": 0,
    },
    # --- Regular articles ---
    {
        "title": "Addis Ababa Metro Expansion Set to Connect Outer Suburbs by 2026",
        "category": "Ethiopia",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The city's light rail network will extend to six new lines, easing congestion for 5 million daily commuters.",
        "content": (
            "ADDIS ABABA — The Ethiopian Capital City Administration has unveiled an ambitious "
            "expansion plan for the Addis Ababa Light Rail Transit system, adding six new lines "
            "that will stretch deep into the city's rapidly growing outer suburbs.\n\n"
            "The expansion is expected to be completed in two phases, with the first phase — "
            "covering three new corridors — due for completion by late 2025. The project, "
            "estimated at $2.4 billion, will be co-financed by the Ethiopian government and "
            "the Chinese Export-Import Bank.\n\n"
            "Urban planners say the expansion is critical to reduce traffic congestion, which "
            "costs the capital an estimated $500 million annually in lost productivity."
        ),
        "image_seed": "addis-metro",
        "days_ago": 1,
    },
    {
        "title": "Ethiopian Coffee Exports Hit Record $1.4 Billion in Fiscal Year 2024",
        "category": "Business",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Specialty coffee from Yirgacheffe and Sidamo commanded premium prices, driving the highest-ever export revenue.",
        "content": (
            "ADDIS ABABA — Ethiopia's coffee exports have reached a record $1.43 billion "
            "in fiscal year 2024, according to the Ethiopian Coffee and Tea Authority, "
            "surpassing the previous record by 18 percent.\n\n"
            "The surge was driven by growing global demand for Ethiopian specialty coffees, "
            "particularly single-origin varieties from the Yirgacheffe, Sidamo, Harrar, "
            "and Jimma regions. European and North American specialty roasters have "
            "significantly increased their orders.\n\n"
            "Coffee remains Ethiopia's largest export commodity, contributing nearly 30 percent "
            "of total foreign exchange earnings. The government has set a target of $2 billion "
            "in annual coffee export revenue by 2030."
        ),
        "image_seed": "ethiopian-coffee",
        "days_ago": 1,
    },
    {
        "title": "Ethiopia's Tech Startup Ecosystem Attracts $200M in Venture Capital",
        "category": "Technology",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Fintech and agri-tech startups in Addis Ababa are drawing unprecedented investor attention from Silicon Valley and Dubai.",
        "content": (
            "ADDIS ABABA — Ethiopian startups raised a combined $200 million in venture capital "
            "funding in 2024, a fourfold increase from 2022, signaling growing confidence in "
            "the country's technology potential.\n\n"
            "Fintech companies led fundraising activity, as Ethiopia's new banking liberalisation "
            "policies opened the sector to private and foreign investment for the first time. "
            "Several agri-tech platforms connecting smallholder farmers to premium export markets "
            "also attracted significant funding.\n\n"
            "The startup boom is being facilitated by iCog Labs, the AAiT Innovation Hub, and "
            "a growing community of diaspora entrepreneurs returning to Addis Ababa."
        ),
        "image_seed": "tech-startup",
        "days_ago": 2,
    },
    {
        "title": "Kenyan President Visits Addis Ababa for Bilateral Trade Talks",
        "category": "Africa",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The two East African nations seek to double bilateral trade to $3 billion over the next five years.",
        "content": (
            "ADDIS ABABA — Kenyan President William Ruto arrived in Addis Ababa on a two-day "
            "state visit aimed at deepening economic ties between Kenya and Ethiopia, two of "
            "East Africa's largest economies.\n\n"
            "The talks centered on removing non-tariff barriers, increasing cross-border energy "
            "trade, and establishing a joint industrial zone near the Moyale border crossing.\n\n"
            "Prime Minister Abiy Ahmed and President Ruto signed four bilateral agreements "
            "covering trade facilitation, infrastructure development, tourism promotion, and "
            "security cooperation."
        ),
        "image_seed": "kenya-ethiopia",
        "days_ago": 2,
    },
    {
        "title": "Ethiopia's National Football Team Qualifies for AFCON 2025",
        "category": "Sports",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The Walias sealed their place in the Africa Cup of Nations with a dramatic 2-1 victory over Tunisia in Addis Ababa.",
        "content": (
            "ADDIS ABABA — Ethiopia's national football team, the Walias, have qualified for "
            "the 2025 Africa Cup of Nations after a tense 2-1 victory over Tunisia at Addis "
            "Ababa Stadium in front of a sold-out crowd of 35,000 fans.\n\n"
            "A late winner from striker Getaneh Kebede in the 87th minute sent the stadium "
            "into rapturous celebrations. It is Ethiopia's first AFCON qualification since 2013.\n\n"
            "Head coach Yohannes Sahle praised the team's resilience: 'This group of players "
            "has worked incredibly hard. Tonight belongs to every Ethiopian who believed in us.'"
        ),
        "image_seed": "ethiopia-football",
        "days_ago": 3,
    },
    {
        "title": "UNESCO Inscribes Lalibela Rock-Hewn Churches on Expanded World Heritage List",
        "category": "Culture",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The 12th-century monolithic churches carved from living rock received enhanced protection under UNESCO's extended mandate.",
        "content": (
            "ADDIS ABABA — UNESCO has expanded its World Heritage designation for the "
            "Lalibela rock-hewn churches in northern Ethiopia, adding new protection for "
            "the surrounding archaeological landscape and pilgrimage routes.\n\n"
            "The site, carved from solid red volcanic rock in the 12th and 13th centuries "
            "under King Lalibela, draws hundreds of thousands of pilgrims and tourists annually "
            "for the Ethiopian Orthodox Timkat (Epiphany) celebration.\n\n"
            "The Ethiopian Heritage Authority has announced a new conservation masterplan "
            "developed in partnership with UNESCO to address threats from climate change, "
            "seismic activity, and increased visitor footfall."
        ),
        "image_seed": "lalibela",
        "days_ago": 3,
    },
    {
        "title": "G20 Nations Pledge $50 Billion Climate Fund for African Green Transition",
        "category": "World",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The landmark climate finance deal, reached at the G20 summit in Rio, will prioritise renewable energy and climate adaptation across the continent.",
        "content": (
            "RIO DE JANEIRO — G20 nations have agreed to establish a $50 billion 'Africa "
            "Green Transition Fund' to support clean energy development and climate adaptation "
            "projects across the continent over the next decade.\n\n"
            "The fund, announced on the final day of the G20 summit in Rio de Janeiro, "
            "will be administered by the African Development Bank and disbursed through "
            "national green investment banks.\n\n"
            "African heads of state present at the summit welcomed the commitment but "
            "stressed that effective disbursement mechanisms — a longstanding weakness of "
            "previous climate finance pledges — must be in place before the end of 2025."
        ),
        "image_seed": "g20-climate",
        "days_ago": 4,
    },
    {
        "title": "Addis Ababa to Host Pan-African Film Festival in November",
        "category": "Culture",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Over 150 films from 40 African countries will screen at the inaugural Addis Film Week, the continent's largest film showcase.",
        "content": (
            "ADDIS ABABA — The Ethiopian Film Commission has announced Addis Ababa as the "
            "inaugural host city for Pan-African Film Week, a new annual festival celebrating "
            "cinema from across the continent.\n\n"
            "The event, scheduled for November 12-19, will feature 153 films across 12 screening "
            "venues, including works from first-time directors and established auteurs. A special "
            "retrospective on Ethiopian cinema will spotlight classics from the 1960s golden era.\n\n"
            "Workshops, industry panels, and a co-production market are also planned, with "
            "the goal of strengthening Africa's film industry infrastructure."
        ),
        "image_seed": "addis-film",
        "days_ago": 4,
    },
    {
        "title": "Ethiopia's New Airline Routes Connect Addis to 10 More African Cities",
        "category": "Business",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Ethiopian Airlines continues its aggressive expansion, now serving 140 destinations across 5 continents.",
        "content": (
            "ADDIS ABABA — Ethiopian Airlines has launched new direct routes connecting Addis "
            "Ababa Bole International Airport to ten additional African cities, reinforcing "
            "the carrier's position as Africa's largest and most profitable airline.\n\n"
            "The new routes include Conakry, Cotonou, Nouakchott, Bangui, and six other "
            "secondary African hubs that previously had no direct connectivity to Ethiopia.\n\n"
            "CEO Mesfin Tasew stated that the expansion is part of a 15-year strategy to make "
            "Ethiopian Airlines the global hub for Africa's growing intra-continental travel "
            "market, which is projected to triple by 2040."
        ),
        "image_seed": "ethiopian-airlines",
        "days_ago": 5,
    },
    {
        "title": "Drought Conditions Worsen Across Tigray and Afar Regions",
        "category": "Ethiopia",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Failed rains for the third consecutive season have triggered food insecurity alerts for 3.2 million people in northern Ethiopia.",
        "content": (
            "ADDIS ABABA — The National Disaster Risk Management Commission has issued a "
            "Level 3 food security alert for the Tigray and Afar regions, where successive "
            "failed rainy seasons have left 3.2 million people in urgent need of assistance.\n\n"
            "Aid agencies report that malnutrition rates among children under five have "
            "exceeded emergency thresholds in several districts. The Ethiopian government "
            "has released emergency food stocks and is coordinating with the UN World "
            "Food Programme for additional support.\n\n"
            "Climate scientists attribute the prolonged drought to a combination of the "
            "El Niño weather pattern and the longer-term drying trend across the Horn "
            "of Africa linked to global climate change."
        ),
        "image_seed": "ethiopia-drought",
        "days_ago": 5,
    },
    {
        "title": "East Africa's Largest Solar Farm Begins Operations in Tigray",
        "category": "Technology",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The 500MW Corbetti Solar Park will provide clean electricity to over 2 million households in northern Ethiopia.",
        "content": (
            "MEKELLE — Ethiopia's largest solar energy installation has commenced commercial "
            "operations in the Tigray region, providing 500 megawatts of clean electricity "
            "to the national grid.\n\n"
            "The Corbetti Solar Park, built by a consortium of Ethiopian and international "
            "renewable energy investors, spans 3,000 hectares and incorporates battery "
            "storage technology to ensure consistent 24-hour power supply.\n\n"
            "The project is part of Ethiopia's Green Legacy Initiative, which aims to "
            "generate 60 percent of the country's electricity from renewable sources by 2030 "
            "while tripling total generation capacity."
        ),
        "image_seed": "solar-ethiopia",
        "days_ago": 6,
    },
    {
        "title": "Nigeria and Ethiopia Sign $5 Billion Infrastructure Partnership",
        "category": "Africa",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Africa's two most populous nations have agreed to co-develop transport, energy, and digital infrastructure projects.",
        "content": (
            "ABUJA — Nigeria and Ethiopia have signed a landmark $5 billion infrastructure "
            "cooperation framework during a state visit by Prime Minister Abiy Ahmed to Abuja.\n\n"
            "The deal covers joint investment in road and rail corridors, undersea fibre-optic "
            "cables connecting East and West Africa, and cross-border renewable energy projects.\n\n"
            "Together, Nigeria and Ethiopia account for nearly 40 percent of sub-Saharan "
            "Africa's combined GDP, and analysts described the partnership as potentially "
            "transformative for continental economic integration."
        ),
        "image_seed": "nigeria-ethiopia",
        "days_ago": 6,
    },
    {
        "title": "Ethiopian Marathon Champion Breaks World Record in Berlin",
        "category": "Sports",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Tigist Assefa shattered her own world record by 47 seconds, finishing the Berlin Marathon in an astonishing 2:09:56.",
        "content": (
            "BERLIN — Ethiopian marathon superstar Tigist Assefa has broken the women's "
            "marathon world record for the second time, crossing the finish line at the "
            "Berlin Marathon in 2 hours, 9 minutes and 56 seconds — shattering her own "
            "previous mark by 47 seconds.\n\n"
            "The 27-year-old from Amhara region led from the 30-kilometre mark, pulling "
            "away from the field with a devastating late surge. The crowd of 50,000 lining "
            "the Unter den Linden boulevard erupted as she crossed the finish line.\n\n"
            "'I knew this was my day,' said Assefa. 'I felt strong throughout. Ethiopia "
            "has given me everything; I run for every Ethiopian woman.'"
        ),
        "image_seed": "marathon-berlin",
        "days_ago": 7,
    },
    {
        "title": "UN Security Council Extends Ethiopia Peacekeeping Mission for 12 Months",
        "category": "World",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The UN mission supporting stability in the Horn of Africa has been renewed, with an expanded civilian protection mandate.",
        "content": (
            "NEW YORK — The United Nations Security Council has unanimously voted to extend "
            "the UNSOM Ethiopia peacekeeping mission for an additional 12 months, with an "
            "enhanced mandate focused on civilian protection and humanitarian access.\n\n"
            "The resolution, sponsored by France and the United Kingdom, also authorised "
            "an increase in the mission's uniformed personnel by 2,000 troops and "
            "100 police advisers.\n\n"
            "Ethiopia's representative to the UN welcomed the renewal, emphasising that "
            "the government remains committed to a peaceful and inclusive political process."
        ),
        "image_seed": "un-security",
        "days_ago": 7,
    },
    {
        "title": "Addis Ababa University Ranks in Top 10 African Universities for Research",
        "category": "Ethiopia",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The university has climbed 40 places in the latest QS African Rankings, recognised for excellence in medical research and engineering.",
        "content": (
            "ADDIS ABABA — Addis Ababa University has entered the top 10 of the QS African "
            "University Rankings for the first time in its history, credited to a surge in "
            "research output, international academic partnerships, and improvements in "
            "graduate employability.\n\n"
            "The university's College of Health Sciences, which is leading Africa-wide "
            "research into tropical disease prevention, and the Addis Ababa Institute of "
            "Technology were singled out for particular commendation.\n\n"
            "Vice-Chancellor Professor Tassew Woldehanna said the ranking reflects a "
            "decade of strategic investment in faculty development and research infrastructure."
        ),
        "image_seed": "aau-university",
        "days_ago": 8,
    },
    {
        "title": "Ethiopia Hosts First-Ever Pan-African Women's Leadership Summit",
        "category": "Culture",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Over 1,000 women leaders from government, business, and civil society gathered in Addis Ababa to shape a new continental agenda.",
        "content": (
            "ADDIS ABABA — Addis Ababa became the focal point for a new chapter in African "
            "women's leadership as more than 1,000 delegates gathered for the inaugural "
            "Pan-African Women's Leadership Summit at the AU Conference Centre.\n\n"
            "Participants included heads of state, cabinet ministers, tech entrepreneurs, "
            "artists, and grassroots activists from 52 African nations. The summit adopted "
            "the 'Addis Declaration' — a binding commitment by signatory governments to "
            "achieve 50 percent women's representation in public institutions by 2030.\n\n"
            "'Africa's future depends on the full participation of women in every sphere "
            "of public life,' said AU Commission Chairperson Moussa Faki Mahamat."
        ),
        "image_seed": "women-summit",
        "days_ago": 9,
    },
    {
        "title": "Ethiopia to Build Africa's First High-Speed Rail Line Between Addis and Djibouti",
        "category": "Business",
        "is_featured": False,
        "is_breaking": False,
        "summary": "The 756km high-speed rail corridor will cut the journey from 12 hours to under 3 hours and transform regional trade.",
        "content": (
            "ADDIS ABABA — The Ethiopian government has signed a framework agreement with "
            "a consortium of European and Chinese engineering firms to develop Africa's "
            "first true high-speed rail line, linking Addis Ababa to the Port of Djibouti.\n\n"
            "The 756-kilometre line will operate at speeds of up to 350 kilometres per hour, "
            "reducing the travel time between the two cities from 12 hours to 2 hours and 40 "
            "minutes. The project will cost an estimated $12 billion and take seven years to complete.\n\n"
            "More than 90 percent of Ethiopia's imports and exports pass through Djibouti, "
            "making the corridor one of the most strategically important infrastructure "
            "projects in East Africa."
        ),
        "image_seed": "high-speed-rail",
        "days_ago": 10,
    },
    {
        "title": "Protest Erupts in Oromia Over Land Rights; Government Calls for Dialogue",
        "category": "Ethiopia",
        "is_featured": False,
        "is_breaking": False,
        "summary": "Thousands took to the streets in Jimma and Shashemene over disputed agricultural land allocations, with authorities urging calm.",
        "content": (
            "ADDIS ABABA — Large protests erupted in several towns in the Oromia region "
            "on Monday over government plans to reallocate agricultural land for a new "
            "industrial zone, drawing thousands of farmers and community leaders into "
            "the streets of Jimma, Shashemene, and Bale Robe.\n\n"
            "The government issued a statement calling for peaceful dialogue and "
            "suspending the land reallocation pending a review by a committee of "
            "regional experts, community representatives, and federal officials.\n\n"
            "The protests, which were largely peaceful, underline the persistent tension "
            "between rapid industrialisation and the land rights of Ethiopia's farming "
            "communities, many of whom hold land under customary tenure systems with "
            "no formal legal title."
        ),
        "image_seed": "oromia-protest",
        "days_ago": 11,
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample Ethiopian news articles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing articles and categories before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Article.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing articles and categories."))

        # Create categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "slug": slugify(cat_data["name"]),
                    "color": cat_data["color"],
                },
            )
            cat_map[cat_data["name"]] = cat
            if created:
                self.stdout.write(f"  Created category: {cat.name}")

        # Create articles
        now = timezone.now()
        created_count = 0
        for data in ARTICLES:
            slug = slugify(data["title"])
            if Article.objects.filter(slug=slug).exists():
                continue

            cat = cat_map.get(data["category"])
            published_at = now - timedelta(days=data["days_ago"], hours=random.randint(0, 12))

            Article.objects.create(
                title=data["title"],
                slug=slug,
                summary=data["summary"],
                content=data["content"],
                image_url=img(data["image_seed"]),
                category=cat,
                published_at=published_at,
                is_featured=data.get("is_featured", False),
                is_breaking=data.get("is_breaking", False),
                views_count=random.randint(100, 15000),
                status="published",
            )
            created_count += 1
            self.stdout.write(f"  Created: {data['title'][:60]}…")

        self.stdout.write(
            self.style.SUCCESS(f"\nDone! Created {created_count} articles across {len(cat_map)} categories.")
        )
