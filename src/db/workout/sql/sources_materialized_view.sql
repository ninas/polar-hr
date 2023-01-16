 CREATE MATERIALIZED VIEW sources_materialized AS select
  s.id,
  s.length,
  s.creator,
  s.name,
  s.sourcetype,
  s.extrainfo,
  s.url,
  array_agg(distinct tt.name) as tags,
  array_agg(distinct te.name) as exercises,
  json_agg(distinct
    case when wm.id is null then null
    else
      (jsonb_build_object(
          'id', wm.id,
          'avghr', wm.avghr,
          'calories', wm.calories,
          'endtime', wm.endtime,
          'maxhr', wm.maxhr,
          'minhr', wm.minhr,
          'notes', wm.notes,
          'sport', wm.sport,
          'starttime', wm.starttime,
          'samples', wm.samples,
          'zone_below_50_lower', wm.zone_below_50_lower,
          'zone_below_50_upper', wm.zone_below_50_upper,
          'zone_below_50_duration', wm.zone_below_50_duration,
          'zone_below_50_percentspentabove', wm.zone_below_50_percentspentabove,
          'zone_50_60_lower', wm.zone_50_60_lower,
          'zone_50_60_upper', wm.zone_50_60_upper,
          'zone_50_60_duration', wm.zone_50_60_duration,
          'zone_50_60_percentspentabove', wm.zone_50_60_percentspentabove,
          'zone_60_70_lower', wm.zone_60_70_lower,
          'zone_60_70_upper', wm.zone_60_70_upper,
          'zone_60_70_duration', wm.zone_60_70_duration,
          'zone_60_70_percentspentabove', wm.zone_60_70_percentspentabove,
          'zone_70_80_lower', wm.zone_70_80_lower,
          'zone_70_80_upper', wm.zone_70_80_upper,
          'zone_70_80_duration', wm.zone_70_80_duration,
          'zone_70_80_percentspentabove', wm.zone_70_80_percentspentabove,
          'zone_80_90_lower', wm.zone_80_90_lower,
          'zone_80_90_upper', wm.zone_80_90_upper,
          'zone_80_90_duration', wm.zone_80_90_duration,
          'zone_80_90_percentspentabove', wm.zone_80_90_percentspentabove,
          'zone_90_100_lower', wm.zone_90_100_lower,
          'zone_90_100_upper', wm.zone_90_100_upper,
          'zone_90_100_duration', wm.zone_90_100_duration,
          'zone_90_100_percentspentabove', wm.zone_90_100_percentspentabove,
          'tags', wm.tags,
          'equipment', wm.equipment
        ))
    end
  ) as workouts
from sources as s
left outer join workouts_sources_through as wst on s.id = wst.sources_id
left outer join workouts_materialized as wm on wst.workouts_id = wm.id
left outer join (select tts.sources_id, tag_tag.name from sources_tags_through as tts join tags as tag_tag on tts.tags_id = tag_tag.id where tag_tag.tagtype <> 'EXERCISE') as tt on s.id = tt.sources_id
left outer join (select ttss.sources_id, tag_exercise.name from sources_tags_through as ttss join tags as tag_exercise on ttss.tags_id = tag_exercise.id where tag_exercise.tagtype = 'EXERCISE') as te on s.id = te.sources_id
group by s.id
order by s.id;
