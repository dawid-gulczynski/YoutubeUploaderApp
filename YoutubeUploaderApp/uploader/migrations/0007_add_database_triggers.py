# Generated manually on 2025-11-23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0006_short_tags_short_tags_count_and_more'),
    ]

    operations = [
        # ========================================================================
        # TRIGGER 1: Auto-update video's shorts_created counter
        # ========================================================================
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER IF NOT EXISTS update_video_shorts_count_on_insert
            AFTER INSERT ON uploader_short
            FOR EACH ROW
            BEGIN
                UPDATE uploader_video
                SET shorts_created = (
                    SELECT COUNT(*) FROM uploader_short WHERE video_id = NEW.video_id
                )
                WHERE id = NEW.video_id;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS update_video_shorts_count_on_insert;"
        ),
        
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER IF NOT EXISTS update_video_shorts_count_on_delete
            AFTER DELETE ON uploader_short
            FOR EACH ROW
            BEGIN
                UPDATE uploader_video
                SET shorts_created = (
                    SELECT COUNT(*) FROM uploader_short WHERE video_id = OLD.video_id
                )
                WHERE id = OLD.video_id;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS update_video_shorts_count_on_delete;"
        ),
        
        # ========================================================================
        # TRIGGER 2: Auto-set published_at when upload_status changes to 'published'
        # ========================================================================
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER IF NOT EXISTS set_published_at_on_status_change
            AFTER UPDATE OF upload_status ON uploader_short
            FOR EACH ROW
            WHEN NEW.upload_status = 'published' AND OLD.upload_status != 'published'
            BEGIN
                UPDATE uploader_short
                SET published_at = datetime('now')
                WHERE id = NEW.id;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS set_published_at_on_status_change;"
        ),
        
        # ========================================================================
        # TRIGGER 3: Auto-update last_analytics_update when stats change
        # ========================================================================
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER IF NOT EXISTS update_analytics_timestamp
            AFTER UPDATE OF views, likes, comments, shares, watch_time_minutes, 
                           average_view_duration, click_through_rate, 
                           engagement_rate, retention_rate ON uploader_short
            FOR EACH ROW
            WHEN (NEW.views != OLD.views OR 
                  NEW.likes != OLD.likes OR 
                  NEW.comments != OLD.comments OR
                  NEW.shares != OLD.shares OR
                  NEW.watch_time_minutes != OLD.watch_time_minutes OR
                  NEW.average_view_duration != OLD.average_view_duration OR
                  NEW.click_through_rate != OLD.click_through_rate OR
                  NEW.engagement_rate != OLD.engagement_rate OR
                  NEW.retention_rate != OLD.retention_rate)
            BEGIN
                UPDATE uploader_short
                SET last_analytics_update = datetime('now')
                WHERE id = NEW.id;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS update_analytics_timestamp;"
        ),
    ]
