"""Diagnostic-only normal completion after the full300round role fixture."""
from bounded_verdict import apply
from live111_camp_role_play import fixture as original_fixture


def fixture(src,hero):
    original_fixture(src,hero)
    apply(src/'main.cpp',(('''        try {
            if(!bc::is_draft()''','''        try {
            if(!bc::is_draft()&&bc::round_number()>=301)bc::resign();
            if(!bc::is_draft()'''),))
