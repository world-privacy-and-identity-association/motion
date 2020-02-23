ALTER TABLE "vote" ADD COLUMN "proxy_id" INTEGER;
UPDATE "vote" SET "proxy_id" = "voter_id";
ALTER TABLE "vote" ALTER COLUMN "proxy_id" SET NOT NULL;
