/**
 * CodeProOJ - Universal Rating & Rank Tier Engine
 * Codeforces-inspired Rating Tiers & Hex Palette
 */

(function (window) {
  'use strict';

  const TIERS = [
    { min: 3000, name: 'Legendary Grandmaster', badge: 'LGM', color: '#ef4444', class: 'tier-lgm', bg: 'rgba(239, 68, 68, 0.15)' },
    { min: 2600, name: 'International Grandmaster', badge: 'IGM', color: '#ef4444', class: 'tier-gm', bg: 'rgba(239, 68, 68, 0.15)' },
    { min: 2400, name: 'Grandmaster',           badge: 'GM',  color: '#ef4444', class: 'tier-gm',  bg: 'rgba(239, 68, 68, 0.15)' },
    { min: 2300, name: 'International Master',  badge: 'IM',  color: '#f97316', class: 'tier-im',  bg: 'rgba(249, 115, 22, 0.15)' },
    { min: 2100, name: 'Master',                badge: 'M',   color: '#f97316', class: 'tier-m',   bg: 'rgba(249, 115, 22, 0.15)' },
    { min: 1900, name: 'Candidate Master',      badge: 'CM',  color: '#a855f7', class: 'tier-cm',  bg: 'rgba(168, 85, 247, 0.15)' },
    { min: 1600, name: 'Expert',                badge: 'EXP', color: '#3b82f6', class: 'tier-exp', bg: 'rgba(59, 130, 246, 0.15)' },
    { min: 1400, name: 'Specialist',            badge: 'SPEC',color: '#10b981', class: 'tier-spec',bg: 'rgba(16, 185, 129, 0.15)' },
    { min: 1200, name: 'Pupil',                 badge: 'PUP', color: '#06b6d4', class: 'tier-pup', bg: 'rgba(6, 182, 212, 0.15)' },
    { min: 1,    name: 'Newbie',                badge: 'NEW', color: '#94a3b8', class: 'tier-new', bg: 'rgba(148, 163, 184, 0.1)' }
  ];

  const UNRATED_TIER = { min: 0, name: 'Unrated', badge: 'UR', color: '#94a3b8', class: 'tier-unrated', bg: 'rgba(148, 163, 184, 0.1)' };

  const CPRating = {
    TIERS,
    UNRATED_TIER,

    getTier(rating) {
      const r = parseInt(rating, 10);
      if (isNaN(r) || r <= 0) return UNRATED_TIER;
      return TIERS.find(t => r >= t.min) || UNRATED_TIER;
    },

    getTierByName(rankName) {
      if (!rankName) return UNRATED_TIER;
      const r = String(rankName).toLowerCase().trim();
      if (r === 'unrated' || r.includes('chưa') || r === '0') return UNRATED_TIER;
      if (r.includes('legendary')) return TIERS[0];
      if (r.includes('grandmaster')) return TIERS[2];
      // CRITICAL: candidate MUST be checked BEFORE master!
      if (r.includes('candidate')) return TIERS[5];
      if (r.includes('master')) return TIERS[4];
      if (r.includes('expert')) return TIERS[6];
      if (r.includes('specialist')) return TIERS[7];
      if (r.includes('pupil')) return TIERS[8];
      if (r.includes('newbie')) return TIERS[9];
      return UNRATED_TIER;
    },

    getColor(rankOrRating, optRating) {
      if (typeof optRating === 'number' && !isNaN(optRating)) {
        return this.getTier(optRating).color;
      }
      if (typeof rankOrRating === 'number' || (!isNaN(parseInt(rankOrRating, 10)) && /^\d+$/.test(String(rankOrRating).trim()))) {
        return this.getTier(rankOrRating).color;
      }
      return this.getTierByName(rankOrRating).color;
    },

    getTierClass(rankOrRating, optRating) {
      if (typeof optRating === 'number' && !isNaN(optRating)) {
        return this.getTier(optRating).class;
      }
      if (typeof rankOrRating === 'number' || (!isNaN(parseInt(rankOrRating, 10)) && /^\d+$/.test(String(rankOrRating).trim()))) {
        return this.getTier(rankOrRating).class;
      }
      return this.getTierByName(rankOrRating).class;
    },

    getRankName(rating) {
      return this.getTier(rating).name;
    }
  };

  // Expose to window globally
  window.CPRating = CPRating;
  window.getRatingColor = (r) => CPRating.getColor(r);
  window.getRankColor = (rank, r) => CPRating.getColor(rank, r);
  window.getTierClass = (tier, r) => CPRating.getTierClass(tier, r);

})(typeof window !== 'undefined' ? window : this);
