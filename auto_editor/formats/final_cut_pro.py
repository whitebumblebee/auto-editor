'''final_cut_pro.py'''

from auto_editor.formats.utils import indent, get_width_height

def fcp_xml(inp, temp, output, clips, chunks, tracks, total_dur, sampleRate,
    audioFile, fps, log):

    pathurl = 'file://' + inp.abspath
    name = inp.name

    def fraction(inp, fps) -> str:
        from fractions import Fraction

        if(inp == 0):
            return '0s'

        if(isinstance(inp, float)):
            inp = Fraction(inp)
        if(isinstance(fps, float)):
            fps = Fraction(fps)

        frac = Fraction(inp, fps).limit_denominator()
        num = frac.numerator
        dem = frac.denominator

        if(dem < 3000):
            factor = int(3000 / dem)

            if(factor == 3000 / dem):
                num *= factor
                dem *= factor
            else:
                # Good enough but has some error that are impacted at speeds such as 150%.
                total = 0
                while(total < frac):
                    total += Fraction(1, 30)
                num = total.numerator
                dem = total.denominator

        return '{}/{}s'.format(num, dem)

    width, height = get_width_height(inp)

    with open(output, 'w', encoding='utf-8') as outfile:

        frame_duration = fraction(1, fps)

        outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        outfile.write('<!DOCTYPE fcpxml>\n\n')
        outfile.write('<fcpxml version="1.9">\n')
        outfile.write('\t<resources>\n')
        outfile.write('\t\t<format id="r1" name="FFVideoFormat{}p{}" '.format(height, fps)+\
            'frameDuration="{}" width="{}" height="{}"'.format(frame_duration, width, height)+\
            ' colorSpace="1-1-1 (Rec. 709)"/>\n')

        outfile.write('\t\t<asset id="r2" name="{}" start="0s" '.format(name)+\
            'hasVideo="1" format="r1" hasAudio="1" '\
            'audioSources="1" audioChannels="2" audioRate="{}">\n'.format(sampleRate))

        outfile.write('\t\t\t<media-rep kind="original-media" '.format()+\
            'src="{}"></media-rep>\n'.format(pathurl))
        outfile.write('\t\t</asset>\n')
        outfile.write('\t</resources>\n')
        outfile.write('\t<library>\n')
        outfile.write('\t\t<event name="auto-editor output">\n')
        outfile.write('\t\t\t<project name="{}">\n'.format(name))
        outfile.write(indent(4,
            '<sequence format="r1" tcStart="0s" tcFormat="NDF" '\
            'audioLayout="stereo" audioRate="48k">',
            '\t<spine>')
        )

        last_dur = 0

        for _, clip in enumerate(clips):
            clip_dur = (clip[1] - clip[0]) / (clip[2] / 100)
            dur = fraction(clip_dur, fps)

            close = '/' if clip[2] == 100 else ''

            if(last_dur == 0):
                outfile.write(indent(6, '<asset-clip name="{}" offset="0s" ref="r2"'.format(name)+\
                ' duration="{}" audioRole="dialogue" tcFormat="NDF"{}>'.format(dur, close)))
            else:
                start = fraction(clip[0] / (clip[2] / 100), fps)
                off = fraction(last_dur, fps)
                outfile.write(indent(6,
                    '<asset-clip name="{}" offset="{}" ref="r2" '.format(name, off)+\
                    'duration="{}" start="{}" audioRole="dialogue" '.format(dur, start)+\
                    'tcFormat="NDF"{}>'.format(close),
                ))

            if(clip[2] != 100):
                # See the "Time Maps" section.
                # https://developer.apple.com/library/archive/documentation/FinalCutProX
                #    /Reference/FinalCutProXXMLFormat/StoryElements/StoryElements.html

                frac_total = fraction(total_dur, fps)
                total_dur_divided_by_speed = fraction((total_dur) / (clip[2] / 100), fps)

                outfile.write(indent(6,
                    '\t<timeMap>',
                    '\t\t<timept time="0s" value="0s" interp="smooth2"/>',
                    '\t\t<timept time="{}" value="{}" interp="smooth2"/>'.format(total_dur_divided_by_speed, frac_total),
                    '\t</timeMap>',
                    '</asset-clip>'
                ))

            last_dur += clip_dur

        outfile.write('\t\t\t\t\t</spine>\n')
        outfile.write('\t\t\t\t</sequence>\n')
        outfile.write('\t\t\t</project>\n')
        outfile.write('\t\t</event>\n')
        outfile.write('\t</library>\n')
        outfile.write('</fcpxml>\n')
