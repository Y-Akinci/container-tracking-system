class Profile:
    def __init__(self, config):
        if config.has_section('simulation'):
            act_profile = config['simulation']['profile']
            self.entries = act_profile.split(';')
            self.section_index = 0
            if len(self.entries[0]) > 0:
                checks = self.entries[0].split(',')
                if len(checks) == 3:
                    return
            raise ValueError("Error: 'profile' is configured incorrectly")
        else:
            raise ValueError("Error: 'simulation' section not found")

    def simulate(self, index, max_index):
        act_pos = index / max_index
        act_values = self.entries[self.section_index]
        pos, temp, hum = act_values.split(',')
        if self.section_index + 1 in range(len(self.entries)):
            next_values = self.entries[self.section_index + 1]
            next_pos, t, h = next_values.split(',')
            if act_pos >= float(next_pos):
                self.section_index += 1
        return temp, hum
