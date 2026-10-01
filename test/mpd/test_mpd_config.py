import re

import lauschkiste.paths


def test_mpd_uses_native_pulse_output():
    config_path = lauschkiste.paths.resource('default-settings', 'mpd.default.conf')
    config = config_path.read_text()
    output_blocks = re.findall(
        r'^audio_output\s*\{(.*?)^\}',
        config,
        flags=re.MULTILINE | re.DOTALL,
    )

    assert len(output_blocks) == 1
    output = output_blocks[0]
    assert re.search(r'^\s*type\s+"pulse"\s*$', output, re.MULTILINE)
    assert re.search(r'^\s*mixer_type\s+"none"\s*$', output, re.MULTILINE)
    assert not re.search(r'^\s*device\s+', output, re.MULTILINE)
