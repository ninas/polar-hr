CREATE MATERIALIZED VIEW workouts_materialized AS select
  w.id,
  w.avghr,
  w.calories,
  w.endtime,
  w.maxhr,
  w.minhr,
  w.notes,
  w.sport,
  w.starttime,
  w.samples,
  w.zone_below_50_lower,
  w.zone_below_50_upper,
  w.zone_below_50_duration,
  w.zone_below_50_percentspentabove,
  w.zone_50_60_lower,
  w.zone_50_60_upper,
  w.zone_50_60_duration,
  w.zone_50_60_percentspentabove,
  w.zone_60_70_lower,
  w.zone_60_70_upper,
  w.zone_60_70_duration,
  w.zone_60_70_percentspentabove,
  w.zone_70_80_lower,
  w.zone_70_80_upper,
  w.zone_70_80_duration,
  w.zone_70_80_percentspentabove,
  w.zone_80_90_lower,
  w.zone_80_90_upper,
  w.zone_80_90_duration,
  w.zone_80_90_percentspentabove,
  w.zone_90_100_lower,
  w.zone_90_100_upper,
  w.zone_90_100_duration,
  w.zone_90_100_percentspentabove,
  array_agg(distinct tags.name) as tags,
  json_agg(distinct
    case when equipment.equipmenttype is null then null
    else (jsonb_build_object(
        'id',equipment.id,
        'magnitude',equipment.magnitude,
        'equipmenttype', equipment.equipmenttype,
        'quantity',equipment.quantity
      ))
    end
  ) as equipment,
  json_agg(distinct
    case when s.id is null then null
    else
      (jsonb_build_object(
          'id', s.id,
          'length', s.length,
          'creator', s.creator,
          'name', s.name,
          'sourcetype', s.sourcetype,
          'url', s.url,
          'tags', array(select name from tags as tts join sources_tags_through as stt on tts.id = stt.tags_id where stt.sources_id = s.id and tts.tagtype <> 'EXERCISE'),
          'exercises', array(select name from tags as tts join sources_tags_through as stt on tts.id = stt.tags_id where stt.sources_id = s.id and tts.tagtype = 'EXERCISE')

      ))
    end
  ) as sources
from workouts as w
left outer join workouts_tags_through as wtt on w.id = wtt.workouts_id
left outer join tags on wtt.tags_id = tags.id
left outer join workouts_equipment_through as wet on w.id = wet.workouts_id
left outer join equipment on wet.equipment_id = equipment.id
left outer join workouts_sources_through as wst on w.id = wst.workouts_id
left outer join sources as s on wst.sources_id = s.id
group by w.id
order by w.id;
